import Foundation
import ImageIO
import UniformTypeIdentifiers

guard CommandLine.arguments.count == 6,
      let frameCount = Int(CommandLine.arguments[2]), frameCount > 1,
      let keyframeDelayMs = Double(CommandLine.arguments[3]), keyframeDelayMs >= 10,
      let subframes = Int(CommandLine.arguments[4]), subframes > 0 else {
    fputs("Usage: swift preview-sequence.swift <frame-directory> <frame-count> <keyframe-delay-ms> <subframes> <output.gif>\n", stderr)
    exit(2)
}

let frameDirectory = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let outputURL = URL(fileURLWithPath: CommandLine.arguments[5])
let sourceFrames: [CGImage] = try (1...frameCount).map { index in
    let url = frameDirectory.appendingPathComponent(String(format: "frame-%03d.png", index))
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        throw NSError(domain: "KurumiPreview", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "Cannot decode \(url.path)"])
    }
    return image
}

let outputDelay = keyframeDelayMs / Double(subframes) / 1000
let canvasWidth: CGFloat = 238
let canvasHeight: CGFloat = 260
let rasterScale: CGFloat = 2
let width = Int(canvasWidth * rasterScale)
let height = Int(canvasHeight * rasterScale)

let colorSpace = CGColorSpaceCreateDeviceRGB()
let bitmapInfo = CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue)
    .union(.byteOrder32Big)
let byteCount = width * height * 4

func visibleBounds(_ image: CGImage) throws -> CGRect {
    let sourceWidth = image.width
    let sourceHeight = image.height
    var sourceBytes = [UInt8](repeating: 0, count: sourceWidth * sourceHeight * 4)
    let drawn = sourceBytes.withUnsafeMutableBytes { buffer -> Bool in
        guard let context = CGContext(data: buffer.baseAddress, width: sourceWidth, height: sourceHeight,
                                      bitsPerComponent: 8, bytesPerRow: sourceWidth * 4,
                                      space: colorSpace, bitmapInfo: bitmapInfo.rawValue) else { return false }
        context.draw(image, in: CGRect(x: 0, y: 0, width: sourceWidth, height: sourceHeight))
        return true
    }
    guard drawn else {
        throw NSError(domain: "KurumiPreview", code: 2,
                      userInfo: [NSLocalizedDescriptionKey: "Cannot inspect frame alpha"])
    }
    let rgba = sourceBytes
    var minX = sourceWidth, minY = sourceHeight, maxX = -1, maxY = -1
    for y in 0..<sourceHeight {
        for x in 0..<sourceWidth where rgba[(y * sourceWidth + x) * 4 + 3] >= 24 {
            minX = min(minX, x); minY = min(minY, y)
            maxX = max(maxX, x); maxY = max(maxY, y)
        }
    }
    guard maxX >= minX, maxY >= minY else {
        throw NSError(domain: "KurumiPreview", code: 3,
                      userInfo: [NSLocalizedDescriptionKey: "Frame has no visible pixels"])
    }
    let left = max(0, minX - 2), bottom = max(0, minY - 2)
    return CGRect(x: left, y: bottom,
                  width: min(sourceWidth - 1, maxX + 2) - left + 1,
                  height: min(sourceHeight - 1, maxY + 2) - bottom + 1)
}

let anchorBounds = try visibleBounds(sourceFrames[0])
let anchorFit = min(canvasHeight * 0.77 / anchorBounds.height,
                    canvasWidth * 0.78 / anchorBounds.width)
func normalize(_ image: CGImage) throws -> CGImage {
    let bounds = try visibleBounds(image)
    guard let cropped = image.cropping(to: bounds),
          let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8,
                                  bytesPerRow: width * 4, space: colorSpace,
                                  bitmapInfo: bitmapInfo.rawValue) else {
        throw NSError(domain: "KurumiPreview", code: 4,
                      userInfo: [NSLocalizedDescriptionKey: "Cannot normalize frame"])
    }
    context.scaleBy(x: rasterScale, y: rasterScale)
    context.interpolationQuality = .high
    let visualWidth = bounds.width * anchorFit
    let visualHeight = bounds.height * anchorFit
    context.draw(cropped, in: CGRect(x: (canvasWidth - visualWidth) / 2,
                                     y: canvasHeight * 0.04,
                                     width: visualWidth, height: visualHeight))
    guard let output = context.makeImage() else {
        throw NSError(domain: "KurumiPreview", code: 5,
                      userInfo: [NSLocalizedDescriptionKey: "Cannot rasterize normalized frame"])
    }
    return output
}
let normalizedFrames = try sourceFrames.map(normalize)

func rgba(_ image: CGImage) throws -> [UInt8] {
    var bytes = [UInt8](repeating: 0, count: byteCount)
    let drawn = bytes.withUnsafeMutableBytes { buffer -> Bool in
        guard let context = CGContext(data: buffer.baseAddress, width: width, height: height,
                                      bitsPerComponent: 8, bytesPerRow: width * 4,
                                      space: colorSpace, bitmapInfo: bitmapInfo.rawValue) else { return false }
        context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
        return true
    }
    guard drawn else {
        throw NSError(domain: "KurumiPreview", code: 6,
                      userInfo: [NSLocalizedDescriptionKey: "Cannot decode RGBA pixels"])
    }
    return bytes
}

func blend(_ left: [UInt8], _ right: [UInt8], amount: Double) throws -> CGImage {
    var bytes = [UInt8](repeating: 0, count: byteCount)
    let t = min(1, max(0, amount))
    for index in 0..<byteCount {
        bytes[index] = UInt8(clamping: Int((Double(left[index]) * (1 - t) + Double(right[index]) * t).rounded()))
    }
    guard let provider = CGDataProvider(data: Data(bytes) as CFData),
          let image = CGImage(width: width, height: height,
                              bitsPerComponent: 8, bitsPerPixel: 32, bytesPerRow: width * 4,
                              space: colorSpace, bitmapInfo: bitmapInfo, provider: provider,
                              decode: nil, shouldInterpolate: true, intent: .defaultIntent) else {
        throw NSError(domain: "KurumiPreview", code: 4,
                      userInfo: [NSLocalizedDescriptionKey: "Cannot create blended image"])
    }
    return image
}

guard let destination = CGImageDestinationCreateWithURL(outputURL as CFURL,
                                                        UTType.gif.identifier as CFString,
                                                        (normalizedFrames.count - 1) * subframes + 1, nil) else {
    throw NSError(domain: "KurumiPreview", code: 7,
                  userInfo: [NSLocalizedDescriptionKey: "Cannot create GIF at \(outputURL.path)"])
}
CGImageDestinationSetProperties(destination, [
    kCGImagePropertyGIFDictionary as String: [kCGImagePropertyGIFLoopCount as String: 0],
] as CFDictionary)

func add(_ image: CGImage, delay: Double, to destination: CGImageDestination) {
    CGImageDestinationAddImage(destination, image, [
        kCGImagePropertyGIFDictionary as String: [
            kCGImagePropertyGIFDelayTime as String: delay,
            kCGImagePropertyGIFUnclampedDelayTime as String: delay,
        ],
    ] as CFDictionary)
}

var previousPixels = try rgba(normalizedFrames[0])
add(normalizedFrames[0], delay: outputDelay, to: destination)
for index in 0..<(normalizedFrames.count - 1) {
    let nextPixels = try rgba(normalizedFrames[index + 1])
    for step in 1..<subframes {
        let t = Double(step) / Double(subframes)
        let eased = t * t * t * (t * (t * 6 - 15) + 10)
        add(try blend(previousPixels, nextPixels, amount: eased), delay: outputDelay, to: destination)
    }
    add(normalizedFrames[index + 1], delay: outputDelay, to: destination)
    previousPixels = nextPixels
}

guard CGImageDestinationFinalize(destination) else {
        throw NSError(domain: "KurumiPreview", code: 8,
                  userInfo: [NSLocalizedDescriptionKey: "Could not finalize GIF"])
}
print("Wrote \((sourceFrames.count - 1) * subframes + 1) frames with eased crossfades to \(outputURL.path)")
