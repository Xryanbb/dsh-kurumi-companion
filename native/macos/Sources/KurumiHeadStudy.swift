import AppKit
import SceneKit

/// Evaluated Blender geometry, including thickness, UVs and vertex normals.
/// The portable package contains no camera-facing image planes or old rig.
final class KurumiHeadStudy {
    struct Bounds: Decodable { let min: [Double]; let max: [Double] }
    struct Material: Decodable {
        let kind: String
        let color: [Double]
        let texture: String?
    }
    struct Mesh: Decodable {
        let name: String
        let vertexOffset: Int, vertexCount: Int, indexOffset: Int, indexCount: Int
        let material: Material
    }
    struct Manifest: Decodable {
        let version: Int
        let model: String
        let bounds: Bounds
        let meshes: [Mesh]
    }
    enum LoadError: LocalizedError {
        case invalid(String)
        var errorDescription: String? {
            if case .invalid(let text) = self { return text }
            return nil
        }
    }

    /// An override supports a local, isolated render check before installation.
    static var runtimeURL: URL? {
        if let path = ProcessInfo.processInfo.environment["DSH_KURUMI_V8_ASSET_ROOT"] {
            return URL(fileURLWithPath: path, isDirectory: true)
        }
        guard let url = Bundle.main.resourceURL?.appendingPathComponent("assets/kurumi3d/v8/runtime", isDirectory: true),
              FileManager.default.fileExists(atPath: url.path) else { return nil }
        return url
    }

    let root: SCNNode
    let camera = SCNNode()
    let meshCount: Int
    let vertexCount: Int
    let triangleCount: Int
    let bounds: Bounds
    private var angle: CGFloat = 0
    private var fromAngle: CGFloat = 0
    private var toAngle: CGFloat = 0
    private var startedAt: Double?
    private var duration: Double = 2.4
    var isAnimating: Bool { startedAt != nil }

    init(url: URL, scene: SCNScene, root: SCNNode) throws {
        let manifest = try JSONDecoder().decode(Manifest.self, from: Data(contentsOf: url.appendingPathComponent("scene.json")))
        guard manifest.version == 1, manifest.model == "kurumi-head-v8",
              manifest.bounds.min.count == 3, manifest.bounds.max.count == 3,
              (manifest.bounds.min + manifest.bounds.max).allSatisfy({ $0.isFinite }),
              zip(manifest.bounds.min, manifest.bounds.max).allSatisfy({ $0 < $1 }),
              !manifest.meshes.isEmpty, manifest.meshes.count < 1024 else {
            throw LoadError.invalid("v8 模型清单不完整")
        }
        let bytes = try Data(contentsOf: url.appendingPathComponent("geometry.bin"), options: .mappedIfSafe)
        self.root = root
        self.bounds = manifest.bounds
        self.meshCount = manifest.meshes.count
        self.vertexCount = manifest.meshes.reduce(0) { $0 + $1.vertexCount }
        self.triangleCount = manifest.meshes.reduce(0) { $0 + $1.indexCount / 3 }
        let center = zip(bounds.min, bounds.max).map { ($0 + $1) / 2 }
        var prepared: [SCNNode] = []
        var materials: [String: SCNMaterial] = [:]
        for mesh in manifest.meshes {
            guard mesh.vertexCount > 0, mesh.vertexCount <= 4_000_000,
                  mesh.indexCount > 0, mesh.indexCount <= 24_000_000, mesh.indexCount % 3 == 0,
                  Self.validRange(mesh.vertexOffset, mesh.vertexCount, 32, bytes.count),
                  Self.validRange(mesh.indexOffset, mesh.indexCount, 4, bytes.count),
                  mesh.material.color.count == 4,
                  mesh.material.color.allSatisfy({ $0.isFinite && $0 >= 0 && $0 <= 4 }) else {
                throw LoadError.invalid("v8 网格数据范围无效：\(mesh.name)")
            }
            let vertices = bytes.subdata(in: mesh.vertexOffset..<(mesh.vertexOffset + mesh.vertexCount * 32))
            let indices = bytes.subdata(in: mesh.indexOffset..<(mesh.indexOffset + mesh.indexCount * 4))
            let validVertices = vertices.withUnsafeBytes { (p: UnsafeRawBufferPointer) in
                (0..<(mesh.vertexCount * 8)).allSatisfy {
                    Float(bitPattern: UInt32(littleEndian: p.loadUnaligned(fromByteOffset: $0 * 4, as: UInt32.self))).isFinite
                }
            }
            let validIndices = indices.withUnsafeBytes { (p: UnsafeRawBufferPointer) in
                (0..<mesh.indexCount).allSatisfy {
                    UInt32(littleEndian: p.loadUnaligned(fromByteOffset: $0 * 4, as: UInt32.self)) < UInt32(mesh.vertexCount)
                }
            }
            guard validVertices, validIndices else { throw LoadError.invalid("v8 顶点或索引无效：\(mesh.name)") }
            func source(_ semantic: SCNGeometrySource.Semantic, _ components: Int, _ offset: Int) -> SCNGeometrySource {
                SCNGeometrySource(data: vertices, semantic: semantic, vectorCount: mesh.vertexCount,
                    usesFloatComponents: true, componentsPerVector: components, bytesPerComponent: 4,
                    dataOffset: offset, dataStride: 32)
            }
            let geometry = SCNGeometry(sources: [source(.vertex, 3, 0), source(.normal, 3, 12), source(.texcoord, 2, 24)],
                elements: [SCNGeometryElement(data: indices, primitiveType: .triangles,
                    primitiveCount: mesh.indexCount / 3, bytesPerIndex: 4)])
            let key = "\(mesh.material.kind)|\(mesh.material.color)|\(mesh.material.texture ?? "")"
            if materials[key] == nil { materials[key] = try Self.material(mesh.material, at: url) }
            geometry.firstMaterial = materials[key]
            let node = SCNNode(geometry: geometry)
            node.name = mesh.name
            node.position = SCNVector3(-center[0], -center[1], -center[2])
            prepared.append(node)
        }
        // Commit to the scene only after all meshes and textures have validated.
        scene.rootNode.addChildNode(root)
        prepared.forEach { root.addChildNode($0) }
        scene.background.contents = NSColor.clear
        camera.name = "portraitCamera"
        camera.camera = SCNCamera()
        camera.camera?.usesOrthographicProjection = true
        camera.camera?.zNear = 0.01
        camera.camera?.zFar = 100
        camera.camera?.wantsHDR = false
        camera.position = SCNVector3(0, 0, 12)
        scene.rootNode.addChildNode(camera)
        let ambient = SCNNode()
        ambient.light = SCNLight(); ambient.light?.type = .ambient
        ambient.light?.intensity = 650
        scene.rootNode.addChildNode(ambient)
        let key = SCNNode()
        key.light = SCNLight(); key.light?.type = .omni
        key.light?.intensity = 550
        key.position = SCNVector3(-3, 5, 6)
        scene.rootNode.addChildNode(key)
        fit(in: NSSize(width: 400, height: 400))
    }

    private static func validRange(_ offset: Int, _ count: Int, _ stride: Int, _ length: Int) -> Bool {
        offset >= 0 && offset % 4 == 0 && offset <= length && count <= (length - offset) / stride
    }

    private static func material(_ definition: Material, at directory: URL) throws -> SCNMaterial {
        let material = SCNMaterial()
        material.name = "v8-" + definition.kind
        let c = definition.color
        func srgb(_ linear: Double) -> CGFloat {
            let value = max(0, min(1, linear))
            return CGFloat(value <= 0.0031308 ? value * 12.92 : 1.055 * pow(value, 1 / 2.4) - 0.055)
        }
        let base = NSColor(srgbRed: srgb(c[0]), green: srgb(c[1]), blue: srgb(c[2]), alpha: CGFloat(c[3]))
        material.diffuse.contents = base
        material.lightingModel = .lambert
        material.specular.contents = NSColor.black
        material.isDoubleSided = false
        material.cullMode = .back
        material.transparencyMode = .aOne
        if definition.kind == "ink" {
            material.lightingModel = .constant
        }
        if let texture = definition.texture {
            guard ["face.png", "hair-albedo.png"].contains(texture),
                  let image = NSImage(contentsOf: directory.appendingPathComponent(texture)) else {
                throw LoadError.invalid("v8 纹理不可读取：\(definition.texture ?? "")")
            }
            material.diffuse.contents = image
            // Blender's image UV origin and SceneKit's NSImage upload differ in V.
            // Preserve the exported coordinates and adapt the texture sampling.
            var textureTransform = SCNMatrix4Identity
            textureTransform.m22 = -1
            textureTransform.m42 = 1
            material.diffuse.contentsTransform = textureTransform
            material.diffuse.wrapS = .clamp; material.diffuse.wrapT = .clamp
            material.diffuse.minificationFilter = .linear; material.diffuse.magnificationFilter = .linear
            material.diffuse.mipFilter = .linear; material.diffuse.maxAnisotropy = 8
            material.lightingModel = .constant
        }
        if definition.kind == "face" {
            guard definition.texture == "face.png" else { throw LoadError.invalid("v8 脸部缺少纹理") }
            material.shaderModifiers = [
                .geometry: """
                #pragma varyings
                float faceCoverage;
                #pragma body
                out.faceCoverage = smoothstep(0.25, 0.75, _geometry.normal.z);
                """,
                .surface: """
                #pragma varyings
                float faceCoverage;
                #pragma body
                float coverage = in.faceCoverage * _surface.diffuse.a;
                _surface.diffuse.rgb = mix(float3(\(c[0]), \(c[1]), \(c[2])), _surface.diffuse.rgb, coverage);
                _surface.diffuse.a = 1.0;
                """
            ]
        } else if definition.kind == "hair" {
            guard definition.texture == "hair-albedo.png" else { throw LoadError.invalid("v8 头发缺少纹理") }
            material.shaderModifiers = [.surface: """
                #pragma body
                _surface.diffuse.rgb *= 1.25;
                _surface.diffuse.a = 1.0;
                """]
        }
        return material
    }

    func fit(in size: NSSize) {
        guard size.width > 1, size.height > 1 else { return }
        let extent = zip(bounds.min, bounds.max).map { $1 - $0 }
        let aspect = Double(size.width / size.height)
        let rotationWidth = hypot(extent[0], extent[2])
        camera.camera?.orthographicScale = max(extent[1], rotationWidth / aspect) * 0.56
    }

    func setView(_ action: String, at time: Double, reducedMotion: Bool = false) {
        let target: CGFloat
        switch action {
        case "front": target = 0
        case "quarter": target = -.pi / 5
        case "left": target = .pi / 2
        case "right": target = -.pi / 2
        case "back": target = .pi
        case "turn": target = angle + .pi * 2
        default: return
        }
        fromAngle = angle
        toAngle = target
        duration = action == "turn" ? 8.0 : 2.4
        if reducedMotion {
            angle = target.truncatingRemainder(dividingBy: .pi * 2)
            root.eulerAngles.y = angle
            startedAt = nil
        } else {
            startedAt = time
        }
    }

    /// Returns true only while an explicit view transition changes the model.
    @discardableResult func update(time: Double, reducedMotion: Bool = false) -> Bool {
        guard let started = startedAt else { return false }
        let t = reducedMotion ? 1 : max(0, min(1, (time - started) / duration))
        let ease = t * t * t * (10 + t * (-15 + 6 * t))
        angle = fromAngle + (toAngle - fromAngle) * CGFloat(ease)
        if t >= 1 { angle = toAngle.truncatingRemainder(dividingBy: .pi * 2); startedAt = nil }
        SCNTransaction.begin(); SCNTransaction.disableActions = true
        root.eulerAngles.y = angle
        SCNTransaction.commit()
        return true
    }
}
