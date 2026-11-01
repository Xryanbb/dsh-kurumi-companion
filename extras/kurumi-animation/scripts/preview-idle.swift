import Foundation
import ImageIO
import UniformTypeIdentifiers

guard CommandLine.arguments.count == 5,
      let frameCount = Int(CommandLine.arguments[2]), frameCount > 0,
      let delayMs = Double(CommandLine.arguments[3]), delayMs >= 10 else {
    fputs("Usage: swift preview-idle.swift <frame-directory> <frame-count> <frame-delay-ms> <output.gif>\n", stderr)
    exit(2)
}

let frameDirectory = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let outputURL = URL(fileURLWithPath: CommandLine.arguments[4])
let names = (1...frameCount).map { String(format: "frame-%03d.png", $0) }
let frames: [CGImage] = try names.map { name in
    let url = frameDirectory.appendingPathComponent(name)
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        throw NSError(domain: "KurumiPreview", code: 1, userInfo: [NSLocalizedDescriptionKey: "Cannot decode \(url.path)"])
    }
    return image
}

let outputFrames = frames.map { (image: $0, delay: delayMs / 1000) }

guard let destination = CGImageDestinationCreateWithURL(outputURL as CFURL, UTType.gif.identifier as CFString, outputFrames.count, nil) else {
    throw NSError(domain: "KurumiPreview", code: 4, userInfo: [NSLocalizedDescriptionKey: "Cannot create GIF at \(outputURL.path)"])
}
CGImageDestinationSetProperties(destination, [
    kCGImagePropertyGIFDictionary as String: [kCGImagePropertyGIFLoopCount as String: 0],
] as CFDictionary)

for frame in outputFrames {
    let properties: [String: Any] = [
        kCGImagePropertyGIFDictionary as String: [
            kCGImagePropertyGIFDelayTime as String: frame.delay,
            kCGImagePropertyGIFUnclampedDelayTime as String: frame.delay,
        ],
    ]
    CGImageDestinationAddImage(destination, frame.image, properties as CFDictionary)
}

guard CGImageDestinationFinalize(destination) else {
    throw NSError(domain: "KurumiPreview", code: 5, userInfo: [NSLocalizedDescriptionKey: "Could not finalize GIF"])
}
print("Wrote \(outputFrames.count) preview frames at \(delayMs) ms each to \(outputURL.path)")
