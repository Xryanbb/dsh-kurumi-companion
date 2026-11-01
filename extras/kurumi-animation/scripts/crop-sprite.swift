import Foundation
import ImageIO
import UniformTypeIdentifiers

guard CommandLine.arguments.count == 5 || CommandLine.arguments.count == 6,
      let columns = Int(CommandLine.arguments[3]), columns > 0,
      let rows = Int(CommandLine.arguments[4]), rows > 0 else {
    fputs("Usage: swift crop-sprite.swift <sheet.png> <output-directory> <columns> <rows> [middle-row-top-inset-px]\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
let outputDirectory = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
guard let source = CGImageSourceCreateWithURL(inputURL as CFURL, nil),
      let sheet = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
    throw NSError(domain: "KurumiSpriteCrop", code: 1,
                  userInfo: [NSLocalizedDescriptionKey: "Could not decode \(inputURL.path)"])
}
try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)
let middleRowTopInset = CommandLine.arguments.count == 6 ? max(0, Int(CommandLine.arguments[5]) ?? 0) : 0

for row in 0..<rows {
    for column in 0..<columns {
        let left = sheet.width * column / columns
        let right = sheet.width * (column + 1) / columns
        let top = sheet.height * row / rows + (row == rows / 2 ? middleRowTopInset : 0)
        let bottom = sheet.height * (row + 1) / rows
        let rect = CGRect(x: left, y: top, width: right - left, height: bottom - top)
        guard let frame = sheet.cropping(to: rect) else {
            throw NSError(domain: "KurumiSpriteCrop", code: 2,
                          userInfo: [NSLocalizedDescriptionKey: "Could not crop row \(row + 1), column \(column + 1)"])
        }
        let index = row * columns + column + 1
        let outputURL = outputDirectory.appendingPathComponent(String(format: "frame-%03d.png", index))
        guard let destination = CGImageDestinationCreateWithURL(outputURL as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw NSError(domain: "KurumiSpriteCrop", code: 3,
                          userInfo: [NSLocalizedDescriptionKey: "Could not write \(outputURL.path)"])
        }
        CGImageDestinationAddImage(destination, frame, nil)
        guard CGImageDestinationFinalize(destination) else {
            throw NSError(domain: "KurumiSpriteCrop", code: 4,
                          userInfo: [NSLocalizedDescriptionKey: "Could not finish \(outputURL.path)"])
        }
    }
}

print("Cropped \(columns * rows) frames from \(inputURL.path)")
