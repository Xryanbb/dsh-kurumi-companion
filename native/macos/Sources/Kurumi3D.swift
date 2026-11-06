import AppKit
import SceneKit

/// Original articulated, volumetric chibi model. No image billboard or downloaded model.
final class Kurumi3DRig {
    let scene = SCNScene()
    let root = SCNNode()
    private(set) var headStudy: KurumiHeadStudy?
    private(set) var loadError: String?
    var isHeadStudy: Bool { headStudy != nil }
    var isHeadStudyRequested: Bool { isHeadStudy || loadError != nil }
    let body = SCNNode()
    let head = SCNNode()
    let leftArm = SCNNode(), rightArm = SCNNode()
    let leftLeg = SCNNode(), rightLeg = SCNNode()
    let leftTail = SCNNode(), rightTail = SCNNode()
    var eyes: [SCNNode] = []
    var lastTime: Double?
    var phase = 0.0
    var wave: CGFloat = 0, think: CGFloat = 0, work: CGFloat = 0, lift: CGFloat = 0
    var turn: CGFloat = 0, walk: CGFloat = 0
    var interactionUntil = 0.0, turnUntil = 0.0, walkUntil = 0.0
    var turnDirection: CGFloat = 1
    var turnStart = -100.0, nodUntil = 0.0
    var nod: CGFloat = 0
    var turnBase: CGFloat = 0
    let black = Kurumi3DRig.material(0x201b26)
    let hair = Kurumi3DRig.material(0x201a24)
    let red = Kurumi3DRig.material(0x931931)
    let lace = Kurumi3DRig.material(0x121019)
    let skin = Kurumi3DRig.material(0xffe1d2)
    let gold = Kurumi3DRig.material(0xdba543)

    static func texture(_ name: String) -> NSImage? {
        guard let url = Bundle.main.resourceURL?.appendingPathComponent("assets/kurumi3d/v2/"+name+".png") else { return nil }
        return NSImage(contentsOf:url)
    }
    static func material(_ rgb: Int) -> SCNMaterial {
        let m = SCNMaterial()
        m.diffuse.contents = NSColor(calibratedRed: CGFloat((rgb >> 16) & 255) / 255,
            green: CGFloat((rgb >> 8) & 255) / 255, blue: CGFloat(rgb & 255) / 255, alpha: 1)
        m.lightingModel = .blinn
        m.specular.contents = NSColor(white: 0.2, alpha: 1)
        m.shininess = 0.22
        m.isDoubleSided = true
        return m
    }
    @discardableResult func sphere(_ parent: SCNNode, _ position: SCNVector3, _ scale: SCNVector3, _ material: SCNMaterial) -> SCNNode {
        let geometry = SCNSphere(radius: 1); geometry.segmentCount = 32; geometry.firstMaterial = material
        let node = SCNNode(geometry: geometry); node.position = position; node.scale = scale; parent.addChildNode(node)
        return node
    }
    func joint(_ node: SCNNode, _ parent: SCNNode, _ position: SCNVector3, _ name: String) {
        node.name = name; node.position = position; parent.addChildNode(node)
    }
    /// Continuous cloth ribbons: the waves are part of the surface, not rows of beads.
    func frill(_ parent: SCNNode, radius: CGFloat, y: CGFloat, width: CGFloat,
               waves: CGFloat, material: SCNMaterial, depth: CGFloat = 0.82) {
        let rows = 12, columns = 288
        surface(parent, rows: rows, columns: columns, material: material) { u, v in
            let a = v * .pi * 2
            let r = radius + u * width + sin(a*waves)*0.012*u
            return SCNVector3(cos(a)*r, y-u*0.09+sin(a*waves)*0.040*u, sin(a)*r*depth)
        }
    }
    /// Finite-difference surface normals follow the actual tapered/ruffled mesh.
    func surface(_ parent: SCNNode, rows: Int, columns: Int, material: SCNMaterial,
                 uv: ((CGFloat, CGFloat, SCNVector3) -> CGPoint)? = nil,
                 sample: (CGFloat, CGFloat) -> SCNVector3) {
        var positions: [SCNVector3] = [], normals: [SCNVector3] = [], indices: [Int32] = []
        var coordinates: [CGPoint] = []
        func difference(_ a: SCNVector3, _ b: SCNVector3) -> SCNVector3 { SCNVector3(a.x-b.x,a.y-b.y,a.z-b.z) }
        for i in 0...rows { for j in 0...columns {
            let u = CGFloat(i)/CGFloat(rows), v = CGFloat(j)/CGFloat(columns), e: CGFloat = 0.0001
            let position = sample(u,v)
            positions.append(position)
            if let uv = uv { coordinates.append(uv(u,v,position)) }
            let du = difference(sample(min(1,u+e),v),sample(max(0,u-e),v))
            let dv = difference(sample(u,v+e),sample(u,v-e))
            let n = SCNVector3(dv.y*du.z-dv.z*du.y,dv.z*du.x-dv.x*du.z,dv.x*du.y-dv.y*du.x)
            let length = sqrt(n.x*n.x+n.y*n.y+n.z*n.z)
            normals.append(length > 0.000000001 ? SCNVector3(n.x/length,n.y/length,n.z/length) : SCNVector3(0,i == 0 ? 1 : -1,0))
        } }
        for i in 0..<rows { for j in 0..<columns {
            let a = Int32(i*(columns+1)+j), b = a+Int32(columns+1)
            indices += [a,a+1,b,a+1,b+1,b]
        } }
        var sources = [SCNGeometrySource(vertices: positions),SCNGeometrySource(normals: normals)]
        if uv != nil { sources.append(SCNGeometrySource(textureCoordinates:coordinates)) }
        let geometry = SCNGeometry(sources: sources,
            elements: [SCNGeometryElement(indices: indices,primitiveType: .triangles)])
        geometry.firstMaterial = material; parent.addChildNode(SCNNode(geometry: geometry))
    }
    /// Small relief shapes retain crisp anime features in a volumetric head.
    @discardableResult func relief(_ parent: SCNNode, path: NSBezierPath, z: CGFloat,
                                  material: SCNMaterial) -> SCNNode {
        // Explicitly tessellate the face art: procedural SCNShape does not
        // expose its vertices before rendering, and a flat polygon cuts into
        // the cheek when only its boundary is projected onto the face.
        path.flatness = 0.001
        path.close()
        let bounds = path.bounds
        let columns = max(4,Int(ceil(bounds.width/0.003))), rows = max(4,Int(ceil(bounds.height/0.003)))
        var vertices: [SCNVector3] = [], indices: [Int32] = []
        for i in 0...rows { for j in 0...columns {
            vertices.append(SCNVector3(bounds.minX+CGFloat(j)/CGFloat(columns)*bounds.width,
                                      bounds.minY+CGFloat(i)/CGFloat(rows)*bounds.height,0))
        } }
        func add(_ a:Int32,_ b:Int32,_ c:Int32) {
            let p = vertices[Int(a)], q = vertices[Int(b)], r = vertices[Int(c)]
            if path.contains(NSPoint(x:(p.x+q.x+r.x)/3,y:(p.y+q.y+r.y)/3)) { indices += [a,b,c] }
        }
        for i in 0..<rows { for j in 0..<columns {
            let a = Int32(i*(columns+1)+j), b = a+Int32(columns+1)
            add(a,a+1,b); add(a+1,b+1,b)
        } }
        let geometry = SCNGeometry(sources:[SCNGeometrySource(vertices:vertices)],
            elements:[SCNGeometryElement(indices:indices,primitiveType:.triangles)])
        geometry.firstMaterial = material
        let node = SCNNode(geometry: geometry); node.position.z = z
        parent.addChildNode(node); return node
    }
    func animeEye(_ parent: SCNNode, clock: Bool) {
        let ink = Self.material(0x21121f), white = Self.material(0xfff5ed)
        ink.lightingModel = .constant; white.lightingModel = .constant
        let highlight = Self.material(0xffffff); highlight.lightingModel = .constant
        let outline = NSBezierPath()
        outline.move(to: NSPoint(x:-0.19,y:0.02))
        outline.curve(to:NSPoint(x:0.185,y:0.03),controlPoint1:NSPoint(x:-0.13,y:0.17),controlPoint2:NSPoint(x:0.12,y:0.18))
        outline.curve(to:NSPoint(x:-0.19,y:0.02),controlPoint1:NSPoint(x:0.18,y:-0.19),controlPoint2:NSPoint(x:-0.13,y:-0.18))
        relief(parent,path:outline,z:0,material:white)
        let sclera = NSBezierPath()
        sclera.move(to:NSPoint(x:-0.169,y:0.015))
        sclera.curve(to:NSPoint(x:0.166,y:0.025),controlPoint1:NSPoint(x:-0.10,y:0.14),controlPoint2:NSPoint(x:0.105,y:0.14))
        sclera.curve(to:NSPoint(x:-0.169,y:0.015),controlPoint1:NSPoint(x:0.15,y:-0.159),controlPoint2:NSPoint(x:-0.12,y:-0.154))
        relief(parent,path:sclera,z:0.006,material:white)
        // Nested iris surfaces provide a dark rim and a warm lower gradient.
        for ring in 0..<12 {
            let t = CGFloat(ring)/11, inset = t*0.028
            let color = clock ? NSColor(calibratedRed:0.48+t*0.47,green:0.27+t*0.43,blue:0.05+t*0.16,alpha:1)
                              : NSColor(calibratedRed:0.30+t*0.48,green:0.025+t*0.10,blue:0.07+t*0.16,alpha:1)
            let material = Self.material(0xffffff); material.diffuse.contents = color; material.lightingModel = .constant
            relief(parent,path:NSBezierPath(ovalIn:NSRect(x:-0.105+inset,y:-0.129+inset*0.4,width:0.22-inset*2,height:0.25-inset*2)),z:0.013+t*0.009,material:material)
        }
        relief(parent,path:NSBezierPath(ovalIn:NSRect(x:-0.023,y:-0.036,width:0.049,height:0.105)),z:0.025,material:ink)
        let lashes = NSBezierPath()
        for k in 0...40 {
            let x = CGFloat(k)/40*0.4-0.2
            let p = NSPoint(x:x,y:0.025+0.12*(1-pow(x/0.2,2)))
            if k == 0 { lashes.move(to:p) } else { lashes.line(to:p) }
        }
        lashes.line(to:NSPoint(x:0.226,y:0.085))
        for k in (0...40).reversed() {
            let x = CGFloat(k)/40*0.4-0.2
            lashes.line(to:NSPoint(x:x,y:0.005+0.085*(1-pow(x/0.2,2))))
        }
        lashes.close()
        relief(parent,path:lashes,z:0.046,material:ink)
        if clock {
            for k in 0..<12 {
                let a = CGFloat(k)/12 * .pi*2
                let tick = NSBezierPath(roundedRect:NSRect(x:-0.003,y:0.085,width:0.006,height:0.018),xRadius:0.002,yRadius:0.002)
                let n = relief(parent,path:tick,z:0.029,material:ink); n.eulerAngles.z = a
            }
            let hand = NSBezierPath(rect:NSRect(x:-0.003,y:-0.005,width:0.006,height:0.088))
            relief(parent,path:hand,z:0.032,material:ink).eulerAngles.z = -0.85
        }
        relief(parent,path:NSBezierPath(ovalIn:NSRect(x:-0.073,y:0.049,width:0.055,height:0.048)),z:0.04,material:highlight)
        relief(parent,path:NSBezierPath(ovalIn:NSRect(x:0.055,y:-0.084,width:0.021,height:0.026)),z:0.04,material:highlight)
    }
    /// Fit the relief to the cheek instead of leaving flat eye plates in profile.
    func conformEye(_ eye: SCNNode) {
        for node in eye.childNodes {
            guard let geometry = node.geometry, let source = geometry.sources(for:.vertex).first else { continue }
            var vertices: [SCNVector3] = [], normals: [SCNVector3] = []
            source.data.withUnsafeBytes { (bytes:UnsafeRawBufferPointer) in
                func component(_ offset:Int) -> CGFloat {
                    if source.bytesPerComponent == 4 { return CGFloat(bytes.loadUnaligned(fromByteOffset:offset,as:Float.self)) }
                    return CGFloat(bytes.loadUnaligned(fromByteOffset:offset,as:Double.self))
                }
                for i in 0..<source.vectorCount {
                    let offset = source.dataOffset+i*source.dataStride
                    let x = component(offset), y = component(offset+source.bytesPerComponent)
                    let oldZ = component(offset+source.bytesPerComponent*2)
                    // Clock ticks have a local rotation: project their rotated points too.
                    let a = node.eulerAngles.z
                    let rx = x*cos(a)-y*sin(a), ry = (x*sin(a)+y*cos(a))*0.96
                    let gx = eye.position.x+rx, gy = eye.position.y+ry
                    let radiusX = CGFloat(0.62)*(1-0.24*pow(max(0,-gy/0.57),1.3))
                    let depth = sqrt(max(0.01,1-pow(gx/radiusX,2)-pow(gy/0.57,2)))*0.48
                    vertices.append(SCNVector3(rx,ry,depth-eye.position.z+0.002+(oldZ+node.position.z)*0.16))
                    normals.append(SCNVector3(gx/(radiusX*radiusX),gy/(0.57*0.57),depth/(0.48*0.48)))
                }
            }
            let curved = SCNGeometry(sources:[SCNGeometrySource(vertices:vertices),SCNGeometrySource(normals:normals)],elements:geometry.elements)
            curved.materials = geometry.materials; node.geometry = curved
            node.position = SCNVector3Zero; node.eulerAngles = SCNVector3Zero
        }
    }
    func curl(_ parent: SCNNode, side: CGFloat, index: Int) {
        let i = CGFloat(index), width = 0.135 + i*0.004
        let p0 = SCNVector3(side*i*0.014,0,i*0.04)
        let p1 = SCNVector3(side*(0.20+i*0.035),-0.28,-0.1+i*0.06)
        let p2 = SCNVector3(side*(0.85-i*0.055),-2.0+i*0.18,0.08+i*0.07)
        let p3 = SCNVector3(side*(0.12+i*0.04),-1.5+i*0.17,0.28+i*0.05)
        surface(parent,rows:40,columns:16,material:hair,uv:{t,v,_ in CGPoint(x:0.42+v*0.12,y:t)}) { t,v in
            let u = 1-t, a = v * .pi*2
            let r = max(0.001,pow(1-t,0.6))
            let c = SCNVector3(u*u*u*p0.x+3*u*u*t*p1.x+3*u*t*t*p2.x+t*t*t*p3.x,
                u*u*u*p0.y+3*u*u*t*p1.y+3*u*t*t*p2.y+t*t*t*p3.y,
                u*u*u*p0.z+3*u*u*t*p1.z+3*u*t*t*p2.z+t*t*t*p3.z)
            let dx = 3*u*u*(p1.x-p0.x)+6*u*t*(p2.x-p1.x)+3*t*t*(p3.x-p2.x)
            let dy = 3*u*u*(p1.y-p0.y)+6*u*t*(p2.y-p1.y)+3*t*t*(p3.y-p2.y)
            let length = max(0.0001,sqrt(dx*dx+dy*dy))
            return SCNVector3(c.x-cos(a)*width*r*dy/length,c.y+cos(a)*width*r*dx/length,c.z+sin(a)*0.038*r)
        }
    }
    /// Tapered curved lock with a full circular section, visible from every angle.
    func lock(_ parent: SCNNode, start: SCNVector3, bend: SCNVector3, end: SCNVector3, width: CGFloat, depth: CGFloat, material: SCNMaterial) {
        surface(parent,rows:36,columns:16,material:material,uv:material === hair ? {t,v,_ in CGPoint(x:0.42+v*0.12,y:t)} : nil) { t,v in
            let u = 1-t, a = v * .pi*2
            let c = SCNVector3(u*u*start.x + 2*u*t*bend.x + t*t*end.x,
                u*u*start.y + 2*u*t*bend.y + t*t*end.y,
                u*u*start.z + 2*u*t*bend.z + t*t*end.z)
            let radius = max(0.001,pow(1-t,0.68)*(0.72+0.40*sin(t * .pi)))
            return SCNVector3(c.x+cos(a)*width*radius,c.y,c.z+sin(a)*depth*radius*(0.85+0.15*cos(v * .pi*6)))
        }
    }
    func skirt(_ parent: SCNNode, top: CGFloat, bottom: CGFloat, y: CGFloat, height: CGFloat, material: SCNMaterial, pleats: CGFloat = 14) {
        surface(parent,rows:28,columns:192,material:material,uv:material === hair ? {t,v,_ in CGPoint(x:0.42+v*0.12,y:t)} : nil) { t,v in
            let a = v * .pi*2
            let fold = cos(a*pleats)*0.032*t + cos(a*pleats*2)*0.008*t*t
            let r = top+(bottom-top)*pow(t,0.72)+fold
            return SCNVector3(cos(a)*r,y-t*height+sin(a*pleats)*0.018*t*t,sin(a)*r*0.82)
        }
    }

    func bow(_ parent: SCNNode, position: SCNVector3, size: CGFloat) {
        let bow = SCNNode(); bow.position = position; parent.addChildNode(bow)
        for side: CGFloat in [-1,1] {
            surface(bow,rows:16,columns:18,material:red) { u,v in
                let y = (v-0.5)*size*(0.30+u*0.82)
                return SCNVector3(side*size*(0.10+u*0.86),y+u*size*0.09,
                    size*(sin(u * .pi)*0.20-cos(v * .pi*2)*u*0.09))
            }
            surface(bow,rows:16,columns:8,material:red) { u,v in
                return SCNVector3(side*size*(0.1+u*0.48)+(v-0.5)*size*0.30,
                    -size*(0.06+u*1.24)+size*0.10*abs(v-0.5)*u,
                    size*(0.06+sin(u * .pi)*0.12+cos(v * .pi*2)*0.035))
            }
        }
        sphere(bow,SCNVector3Zero,SCNVector3(size*0.2,size*0.24,size*0.2),red)
    }
    func hairCap() {
        var vertices: [SCNVector3] = [], normals: [SCNVector3] = [], indices: [Int32] = []
        var coordinates: [CGPoint] = []
        let rows = 32, columns = 64
        for i in 0...rows { for j in 0...columns {
            let a = CGFloat(j)/CGFloat(columns)*CGFloat.pi*2
            let front = max(0,sin(a))
            let theta = CGFloat(i)/CGFloat(rows)*(2.65-front*1.75)
            let x = sin(theta)*cos(a), y = cos(theta), z = sin(theta)*sin(a)
            vertices.append(SCNVector3(x*0.66,y*0.635+0.035,z*0.53-0.01))
            normals.append(SCNVector3(x,y,z))
            coordinates.append(CGPoint(x:0.3+CGFloat(j)/CGFloat(columns)*0.3,y:CGFloat(i)/CGFloat(rows)))
        } }
        for i in 0..<rows { for j in 0..<columns {
            let a = Int32(i*(columns+1)+j), b = a+Int32(columns+1)
            indices += [a,a+1,b,a+1,b+1,b]
        } }
        let geometry = SCNGeometry(sources: [SCNGeometrySource(vertices: vertices), SCNGeometrySource(normals: normals), SCNGeometrySource(textureCoordinates:coordinates)], elements: [SCNGeometryElement(indices: indices, primitiveType: .triangles)])
        geometry.firstMaterial = hair; head.addChildNode(SCNNode(geometry: geometry))
    }
    init() {
        scene.background.contents = NSColor.clear
        if let package = KurumiHeadStudy.runtimeURL {
            do {
                headStudy = try KurumiHeadStudy(url: package, scene: scene, root: root)
            } catch {
                loadError = error.localizedDescription
                FileHandle.standardError.write(Data("Kurumi v8 load failed: \(error.localizedDescription)\n".utf8))
            }
            // A broken requested v8 package must not silently show the old model.
            return
        }
        let faceTexture = Self.texture("face")
        let faceMaterial = Self.material(0xfff0e5)
        if let texture = faceTexture {
            faceMaterial.name = "kurumi-face-v2"
            faceMaterial.diffuse.contents = texture
            faceMaterial.diffuse.wrapS = .clamp; faceMaterial.diffuse.wrapT = .clamp
            faceMaterial.lightingModel = .constant
        }
        if let texture = Self.texture("hair") {
            hair.name = "kurumi-hair-v2"; hair.diffuse.contents = texture
            hair.lightingModel = .lambert
            hair.specular.contents = NSColor.black
            hair.diffuse.minificationFilter = .linear; hair.diffuse.magnificationFilter = .linear
            hair.diffuse.mipFilter = .linear; hair.diffuse.maxAnisotropy = 16
        }
        scene.rootNode.addChildNode(root)
        joint(body,root,SCNVector3(0,1.22,0),"torso")
        // Match the installed skin's short torso and very short visible legs.
        body.scale = SCNVector3(1,0.83,1)
        joint(head,body,SCNVector3(0,1.34,0),"neck")
        head.scale = SCNVector3(1.04,1.20,1.04)
        surface(head,rows:64,columns:112,material:faceMaterial,uv:{_,_,p in CGPoint(x:p.x/1.22+0.5,y:0.43-p.y/1.1)}) { u,v in
            let theta = u * .pi, a = v * .pi*2
            let lower = max(0,-cos(theta))
            let taper = 1-0.14*pow(lower,1.3)
            return SCNVector3(sin(theta)*cos(a)*0.62*taper,cos(theta)*0.57,
                sin(theta)*sin(a)*0.48)
        }
        // Back of the coiffure and pointed fringe are actual curved solids.
        sphere(head,SCNVector3(0,0.05,-0.18),SCNVector3(0.655,0.64,0.43),hair)
        hairCap()
        // Individually swept fringe sections, with a broad central asymmetric lock.
        let fringe: [(CGFloat,CGFloat,CGFloat,CGFloat,CGFloat)] = [
            (-0.48,-0.57,-0.19,0.13,0.025),
            (-0.29,-0.38,-0.12,0.145,0.025),
            (-0.13,-0.20,-0.06,0.14,0.022),
            (0.03,0.08,-0.20,0.205,0.030),
            (0.28,0.43,-0.09,0.15,0.023),
            (0.45,0.58,-0.26,0.12,0.024)
        ]
        for (startX,endX,endY,width,depth) in fringe {
            lock(head,start:SCNVector3(startX*0.65,0.59,0.16),
                 bend:SCNVector3(startX-0.045,0.24,0.565),
                 end:SCNVector3(endX,endY,0.465),width:width,depth:depth,material:hair)
        }
        for side: CGFloat in [-1,1] {
            lock(head,start:SCNVector3(side*0.54,0.35,0.18),bend:SCNVector3(side*0.69,-0.10,0.25),end:SCNVector3(side*0.49,-0.58,0.20),width:0.12,depth:0.11,material:hair)
            let tail = side < 0 ? leftTail : rightTail
            joint(tail,head,SCNVector3(side*0.59,0.22,-0.10),side < 0 ? "hair.left" : "hair.right")
            for i in 0..<5 {
                curl(tail,side:side,index:i)
            }
            bow(head,position:SCNVector3(side*0.63,0.18,0.10),size:0.20)
        }
        // Front-facing bonnet band follows the approved reference's broad ribbon lattice.
        func bonnet(_ angle: CGFloat, _ radius: CGFloat, _ depth: CGFloat) -> SCNVector3 {
            SCNVector3(cos(angle)*radius, 0.04+sin(angle)*radius, depth)
        }
        surface(head,rows:12,columns:144,material:lace) { u,v in
            bonnet(v * .pi, 0.55+u*0.12, 0.36-u*0.055)
        }
        for edge: CGFloat in [0,1] {
            surface(head,rows:8,columns:144,material:red) { u,v in
                let radius = 0.55+edge*0.12+(edge == 0 ? -1 : 1)*u*0.045
                return bonnet(v * .pi,radius,0.37-edge*0.055+sin(v * .pi*26)*0.022*u)
            }
        }
        for i in 0..<12 {
            for direction: CGFloat in [-1,1] {
                surface(head,rows:3,columns:16,material:red) { u,v in
                    let angle = (CGFloat(i)+v)/12 * .pi
                    let r = 0.56 + (direction > 0 ? v : 1-v)*0.10 + (u-0.5)*0.012
                    return bonnet(angle,r,0.385-(r-0.55)*0.45)
                }
            }
        }
        if faceTexture == nil {
        for side: CGFloat in [-1,1] {
            let eye = SCNNode(); joint(eye,head,SCNVector3(side*0.248,-0.155,0.448),side < 0 ? "eye.red" : "eye.clock")
            eyes.append(eye)
            animeEye(eye,clock:side > 0)
            conformEye(eye)
            sphere(head,SCNVector3(side*0.35,-0.30,0.335),SCNVector3(0.065,0.018,0.003),Self.material(0xefb4b0))
        }
        sphere(head,SCNVector3(0,-0.265,0.425),SCNVector3(0.010,0.009,0.003),skin)
        let smile = NSBezierPath()
        smile.move(to:NSPoint(x:-0.065,y:-0.365))
        smile.curve(to:NSPoint(x:0.075,y:-0.349),controlPoint1:NSPoint(x:-0.02,y:-0.391),controlPoint2:NSPoint(x:0.045,y:-0.383))
        smile.curve(to:NSPoint(x:-0.065,y:-0.365),controlPoint1:NSPoint(x:0.035,y:-0.369),controlPoint2:NSPoint(x:-0.02,y:-0.381))
        relief(head,path:smile,z:0.371,material:Self.material(0x9b4c4c))
        }
        sphere(body,SCNVector3(0,0.33,0),SCNVector3(0.32,0.32,0.215),black)
        sphere(body,SCNVector3(0,0.60,0),SCNVector3(0.31,0.14,0.18),skin)
        sphere(body,SCNVector3(0,0.30,0.18),SCNVector3(0.13,0.23,0.045),black)
        for side: CGFloat in [-1,1] {
            let strap = SCNNode(geometry:SCNCapsule(capRadius:0.014,height:0.19))
            strap.position = SCNVector3(side*0.23,0.58,0.12); strap.geometry?.firstMaterial = lace
            strap.eulerAngles.z = side*0.18; body.addChildNode(strap)
            sphere(body,SCNVector3(side*0.14,0.44,0.19),SCNVector3(0.16,0.11,0.085),red)
            for k in 0...2 {
                surface(body,rows:12,columns:6,material:black) { u,v in
                    let x = side*0.14+CGFloat(k-1)*0.075+(v-0.5)*0.030+side*(u-0.5)*0.032
                    let y = 0.35+u*0.18
                    let z = 0.19+0.087*sqrt(max(0.01,1-pow((x-side*0.14)/0.16,2)-pow((y-0.44)/0.11,2)))
                    return SCNVector3(x,y,z)
                }
            }
            // Gathered upper neckline, curved around each bodice panel.
            surface(body,rows:8,columns:64,material:lace) { u,v in
                let a = v * .pi
                return SCNVector3(side*0.14+cos(a)*0.17,0.46+sin(a)*0.10+u*0.035+sin(a*16)*u*0.012,0.225+u*0.025)
            }
        }
        // Corset lacing.
        for i in 0..<4 {
            let y = CGFloat(i)*0.08+0.12
            sphere(body,SCNVector3(-0.07,y,0.229),SCNVector3(0.012,0.012,0.01),gold)
            sphere(body,SCNVector3(0.07,y,0.229),SCNVector3(0.012,0.012,0.01),gold)
            for direction: CGFloat in [-1,1] {
                let laceLine = SCNNode(geometry: SCNCapsule(capRadius: 0.006, height: 0.16))
                laceLine.geometry?.firstMaterial = red
                laceLine.position = SCNVector3(0,y+0.035,0.237)
                laceLine.eulerAngles.z = direction*1.06
                body.addChildNode(laceLine)
            }
        }
        sphere(body,SCNVector3(0,0.67,0),SCNVector3(0.12,0.12,0.11),skin)
        bow(body,position:SCNVector3(0,0.67,0.15),size:0.09)
        skirt(body,top:0.24,bottom:0.74,y:0.06,height:0.70,material:black,pleats:20)
        skirt(body,top:0.39,bottom:0.72,y:-0.16,height:0.42,material:red,pleats:20)
        skirt(body,top:0.28,bottom:0.60,y:0.06,height:0.37,material:black,pleats:16)
        frill(body,radius:0.745,y:-0.64,width:0.08,waves:24,material:lace)
        frill(body,radius:0.73,y:-0.56,width:0.06,waves:24,material:red)
        frill(body,radius:0.67,y:-0.47,width:0.06,waves:24,material:lace)
        frill(body,radius:0.61,y:-0.31,width:0.07,waves:22,material:lace)
        frill(body,radius:0.57,y:-0.26,width:0.06,waves:22,material:red)
        // Bodice collar, an inset apron panel and the back bow complete all views.
        frill(body,radius:0.11,y:0.67,width:0.08,waves:12,material:lace,depth:0.9)
        bow(body,position:SCNVector3(0,0.03,-0.29),size:0.27)
        for side: CGFloat in [-1,1] {
            lock(body,start:SCNVector3(side*0.15,0.06,0.255),bend:SCNVector3(side*0.19,-0.18,0.47),end:SCNVector3(side*0.30,-0.36,0.52),width:0.09,depth:0.025,material:red)
        }
        bow(body,position:SCNVector3(0,0.02,0.27),size:0.23)
        for side: CGFloat in [-1,1] {
            let arm = side < 0 ? leftArm : rightArm
            joint(arm,body,SCNVector3(side*0.33,0.49,0),side < 0 ? "shoulder.left" : "shoulder.right")
            sphere(arm,SCNVector3(0,0.01,0),SCNVector3(0.10,0.11,0.10),skin)
            sphere(arm,SCNVector3(0,-0.19,0),SCNVector3(0.13,0.20,0.13),black)
            skirt(arm,top:0.064,bottom:0.12,y:-0.31,height:0.16,material:black,pleats:10)
            frill(arm,radius:0.11,y:-0.46,width:0.025,waves:12,material:red,depth:1)
            sphere(arm,SCNVector3(0,-0.53,0.02),SCNVector3(0.073,0.09,0.065),skin)
            bow(arm,position:SCNVector3(0,-0.14,0.13),size:0.08)
            let leg = side < 0 ? leftLeg : rightLeg
            joint(leg,body,SCNVector3(side*0.18,-0.32,0),side < 0 ? "hip.left" : "hip.right")
            sphere(leg,SCNVector3(0,-0.24,0),SCNVector3(0.09,0.28,0.09),skin)
            frill(leg,radius:0.095,y:-0.38,width:0.025,waves:10,material:lace,depth:1)
            sphere(leg,SCNVector3(0,-0.45,0),SCNVector3(0.093,0.17,0.094),lace)
            sphere(leg,SCNVector3(0,-0.59,0.06),SCNVector3(0.125,0.10,0.18),black)
            bow(leg,position:SCNVector3(0,-0.55,0.2),size:0.065)
        }
        leftArm.eulerAngles.z = -0.38; rightArm.eulerAngles.z = 0.38
        let camera = SCNNode(); camera.camera = SCNCamera()
        camera.camera!.usesOrthographicProjection = true; camera.camera!.orthographicScale = 1.85
        camera.camera!.zNear = 0.1; camera.camera!.zFar = 50
        camera.name = "portraitCamera"; camera.position = SCNVector3(0,1.60,8)
        scene.rootNode.addChildNode(camera)
        let ambient = SCNNode(); ambient.light = SCNLight(); ambient.light!.type = .ambient; ambient.light!.intensity = 500
        scene.rootNode.addChildNode(ambient)
        let key = SCNNode(); key.light = SCNLight(); key.light!.type = .omni; key.light!.intensity = 750
        key.position = SCNVector3(-3,5,5); scene.rootNode.addChildNode(key)
        let rim = SCNNode(); rim.light = SCNLight(); rim.light!.type = .omni; rim.light!.intensity = 500
        rim.light!.color = NSColor(calibratedRed: 1, green: 0.65, blue: 0.65, alpha: 1)
        rim.position = SCNVector3(3,3,-3); scene.rootNode.addChildNode(rim)
    }
    func interact(_ action: String, at time: Double) {
        if isHeadStudyRequested { return }
        if action == "turn" { turnBase = turn; turnDirection *= -1; turnStart = time; turnUntil = time+3 }
        else if action == "nod" { nodUntil = time+2.6 }
        else if action == "walk" { walkUntil = time+4 }
        else { interactionUntil = time+2.4 }
    }
    func update(time: Double, state: String, dragging: Bool, reduced: Bool) {
        if isHeadStudyRequested {
            headStudy?.update(time: time, reducedMotion: reduced)
            return
        }
        let dt = max(0,min(0.1,time-(lastTime ?? time))); lastTime = time
        phase += reduced ? 0 : dt
        let t = CGFloat(phase), blend = CGFloat(1-exp(-dt*6))
        func damp(_ value: inout CGFloat, _ target: CGFloat) { value += (target-value)*blend }
        damp(&wave, !reduced && (state == "SUCCESS" || time < interactionUntil) ? 1 : 0)
        damp(&think, state == "THINKING" || state == "WAITING" ? 1 : 0)
        damp(&work, state == "WORKING" ? 1 : 0)
        damp(&lift, dragging ? 1 : 0)
        let progress = min(1,max(0,(time-turnStart)/3))
        let eased = progress*progress*progress*(10+progress*(-15+6*progress))
        turn = reduced || turnStart < 0 ? 0 : turnBase+turnDirection*CGFloat.pi*2*CGFloat(eased)
        damp(&nod, !reduced && time < nodUntil ? 1 : 0)
        damp(&walk, !reduced && time < walkUntil ? 1 : 0)
        SCNTransaction.begin(); SCNTransaction.disableActions = true
        root.eulerAngles = SCNVector3(0,turn + (reduced ? 0 : sin(t*0.55)*0.12),0)
        root.position.y = (reduced ? 0 : sin(t*1.8)*0.018) + lift*0.12 + walk*abs(sin(t*6))*0.045
        body.eulerAngles = SCNVector3(lift * -0.10, sin(t*0.8)*0.035, lift*sin(t*5)*0.08 + sin(t*1.2)*0.018)
        head.eulerAngles = SCNVector3(think*0.10 + work*0.12 + nod*sin(t*4)*0.16, sin(t*0.7)*0.055, think*0.14 + wave*sin(t*2)*0.035)
        leftArm.eulerAngles = SCNVector3(-work*0.7-lift*0.1-wave*0.8,0,-0.38-wave*1.7-wave*sin(t*7)*0.25-lift*2.5)
        rightArm.eulerAngles = SCNVector3(-think*0.9-work*0.7,0,0.38-think*2.1+lift*2.5)
        leftLeg.eulerAngles.x = sin(t*6)*walk*0.48+lift*0.18
        rightLeg.eulerAngles.x = -sin(t*6)*walk*0.48-lift*0.16
        leftTail.eulerAngles = SCNVector3(sin(t*1.8)*0.07 + lift*0.2,0,sin(t*1.5)*0.07+lift*0.13)
        rightTail.eulerAngles = SCNVector3(sin(t*1.7+1)*0.06+lift*0.2,0,sin(t*1.4+1.3)*0.07-lift*0.13)
        let blinkPhase = phase.truncatingRemainder(dividingBy: 4.7)
        let blink = reduced ? CGFloat(1) : CGFloat(1-0.94*exp(-pow((blinkPhase-4.3)/0.08,2)))
        for eye in eyes { eye.scale.y = blink }
        SCNTransaction.commit()
    }
}

/// Let the enclosing PetView retain all dragging / right-click hit handling.
final class Kurumi3DView: SCNView {
    let rig = Kurumi3DRig()
    override init(frame: NSRect) {
        super.init(frame: frame, options: nil)
        scene = rig.scene; backgroundColor = .clear
        wantsLayer = true; layer?.isOpaque = false
        antialiasingMode = .multisampling4X; preferredFramesPerSecond = 60
        isPlaying = !rig.isHeadStudyRequested
        rendersContinuously = !rig.isHeadStudyRequested
        if let study = rig.headStudy {
            pointOfView = study.camera
            study.fit(in: frame.size)
        }
        if let error = rig.loadError {
            let label = NSTextField(wrappingLabelWithString: "v8 头部小样加载失败\n\(error)")
            label.textColor = .white
            label.alignment = .center
            label.frame = NSRect(x: 8, y: max(8, frame.height / 2 - 45), width: max(20, frame.width - 16), height: 90)
            label.autoresizingMask = [.width, .minYMargin, .maxYMargin]
            addSubview(label)
        }
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) unsupported") }
    override func setFrameSize(_ newSize: NSSize) {
        super.setFrameSize(newSize)
        rig.headStudy?.fit(in: newSize)
    }
    override func hitTest(_ point: NSPoint) -> NSView? { nil }
}
