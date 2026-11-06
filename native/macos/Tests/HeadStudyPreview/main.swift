// Standalone native geometry/render check. It does not start or change DSH.
// swiftc Sources/KurumiHeadStudy.swift Tests/HeadStudyPreview/main.swift \
//   -framework AppKit -framework SceneKit -framework Metal -o /tmp/head-study-preview
// /tmp/head-study-preview path/to/v8/runtime path/to/output [--validate-only]
import AppKit
import SceneKit
import Metal

guard CommandLine.arguments.count >= 3 else {
    fputs("Usage: head-study-preview <runtime-directory> <output-directory> [--validate-only]\n", stderr)
    exit(2)
}
do {
    let source = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
    let output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
    let scene = SCNScene(), root = SCNNode()
    let study = try KurumiHeadStudy(url: source, scene: scene, root: root)
    precondition(study.meshCount > 0 && study.vertexCount > 0 && study.triangleCount > 0)
    let start = root.eulerAngles
    precondition(!study.update(time: 0))
    precondition(!study.update(time: 90))
    precondition(root.eulerAngles.x == start.x && root.eulerAngles.y == start.y && root.eulerAngles.z == start.z)
    study.setView("turn", at: 100)
    precondition(study.isAnimating)
    precondition(study.update(time: 104))
    precondition(abs(root.eulerAngles.y - .pi) < 0.001)
    precondition(study.update(time: 108))
    precondition(!study.isAnimating && abs(root.eulerAngles.y) < 0.001)
    precondition(!study.update(time: 200))
    try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
    var views: [String] = []
    var renderChecks: [String: [String: Int]] = [:]
    if !CommandLine.arguments.contains("--validate-only") {
        _ = NSApplication.shared
        guard let device = MTLCreateSystemDefaultDevice() else { throw KurumiHeadStudy.LoadError.invalid("No Metal device") }
        let renderer = SCNRenderer(device: device, options: nil)
        renderer.scene = scene; renderer.pointOfView = study.camera
        let size = NSSize(width: 720, height: 720)
        study.fit(in: size)
        for action in ["front", "quarter", "right", "back"] {
            study.setView(action, at: 0, reducedMotion: true)
            let image = renderer.snapshot(atTime: 0, with: size, antialiasingMode: .multisampling4X)
            guard let tiff = image.tiffRepresentation,
                  let raster = NSBitmapImageRep(data: tiff),
                  let png = raster.representation(using: .png, properties: [:]) else {
                throw KurumiHeadStudy.LoadError.invalid("Snapshot failed: \(action)")
            }
            var visible = 0, magenta = 0
            for y in stride(from: 0, to: raster.pixelsHigh, by: 4) {
                for x in stride(from: 0, to: raster.pixelsWide, by: 4) {
                    guard let color = raster.colorAt(x: x, y: y)?.usingColorSpace(.sRGB), color.alphaComponent > 0.5 else { continue }
                    visible += 1
                    if color.redComponent > 0.9 && color.greenComponent < 0.15 && color.blueComponent > 0.9 { magenta += 1 }
                }
            }
            guard visible > 100, magenta < max(10, visible / 100) else {
                throw KurumiHeadStudy.LoadError.invalid("Empty render or shader fallback color: \(action)")
            }
            renderChecks[action] = ["visibleSamples": visible, "shaderFallbackSamples": magenta]
            try png.write(to: output.appendingPathComponent(action + ".png"))
            views.append(action)
        }
    }
    let report: [String: Any] = ["meshCount": study.meshCount, "vertices": study.vertexCount,
        "triangles": study.triangleCount, "idleStatic": true, "turnSeconds": 8,
        "turnReturnsStationary": true, "renderedViews": views, "renderChecks": renderChecks]
    let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
    try data.write(to: output.appendingPathComponent("native-check.json"))
    print(String(data: data, encoding: .utf8)!)
} catch {
    fputs("Head study check failed: \(error.localizedDescription)\n", stderr)
    exit(1)
}
