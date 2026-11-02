"""Build a stylized, editable 3D Kurumi chibi for the DSH desktop pet.

Run with the project's bundled Blender executable:
  Blender --background --python assets/kurumi3d/build_kurumi_v3.py

The approved sprite is a visual proportion guide. The model is original
geometry; the face/hair textures are the existing project assets.
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "kurumi3d" / "v3"
TEXTURES = ROOT / "assets" / "kurumi3d" / "v2"
OUT.mkdir(parents=True, exist_ok=True)


def mat(name, color, roughness=0.62, metallic=0.0, image=None, emission=0.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Specular IOR Level"].default_value = 0.25
    if image:
        img = bpy.data.images.load(str(image), check_existing=True)
        img.pack()
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = img
        texture.interpolation = "Linear"
        texture.extension = "EXTEND"
        links.new(texture.outputs["Color"], shader.inputs["Base Color"])
        if emission > 0:
            links.new(texture.outputs["Color"], shader.inputs["Emission Color"])
            shader.inputs["Emission Strength"].default_value = emission
    else:
        shader.inputs["Base Color"].default_value = (*color, 1.0)
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def smooth(obj):
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def sphere(name, loc, scale, material, segments=48, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    return smooth(obj)


def curve(name, points, radius, material, radii=None, resolution=16):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = resolution
    data.bevel_depth = radius
    data.bevel_resolution = 5
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for i, (bp, point) in enumerate(zip(spline.bezier_points, points)):
        bp.co = point
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
        if radii:
            bp.radius = radii[i]
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def tapered_mesh(name, points, widths, material, sides=12, depth_ratio=0.56):
    """A softly rounded, pointed ribbon lock swept along a Bezier path."""
    centers = [Vector(p) for p in points]
    # Catmull-Rom samples retain the authored silhouette and avoid faceted locks.
    samples = []
    sample_widths = []
    per_segment = 12
    for seg in range(len(centers) - 1):
        p0 = centers[max(0, seg - 1)]
        p1, p2 = centers[seg], centers[seg + 1]
        p3 = centers[min(len(centers) - 1, seg + 2)]
        for step in range(per_segment):
            t = step / per_segment
            t2, t3 = t * t, t * t * t
            c = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2*p0 - 5*p1 + 4*p2 - p3) * t2 + (-p0 + 3*p1 - 3*p2 + p3) * t3)
            w = widths[seg] * (1-t) + widths[seg + 1] * t
            samples.append(c)
            sample_widths.append(w)
    samples.append(centers[-1])
    sample_widths.append(widths[-1])

    verts, faces = [], []
    uv_layer = []
    for i, c in enumerate(samples):
        before = samples[max(0, i - 1)]
        after = samples[min(len(samples) - 1, i + 1)]
        tangent = (after - before).normalized()
        # Most locks lie in XZ; this normal makes their broad face face forward.
        side = Vector((tangent.z, 0, -tangent.x)).normalized()
        depth = Vector((0, 1, 0))
        width = max(0.002, sample_widths[i])
        for j in range(sides):
            a = 2 * math.pi * j / sides
            v = c + side * (math.cos(a) * width) + depth * (math.sin(a) * width * depth_ratio)
            verts.append(tuple(v))
            uv_layer.append((j / sides, i / max(1, len(samples)-1)))
    for i in range(len(samples) - 1):
        for j in range(sides):
            a = i*sides+j
            b = i*sides+(j+1)%sides
            c = (i+1)*sides+(j+1)%sides
            d = (i+1)*sides+j
            faces.append((a, b, c, d))
    faces.append(tuple(range(sides-1, -1, -1)))
    faces.append(tuple((len(samples)-1)*sides+j for j in range(sides)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for p in mesh.polygons:
        p.use_smooth = True
    uv = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        uv.data[loop.index].uv = uv_layer[loop.vertex_index]
    bevel = obj.modifiers.new("Silky rounded edge", "BEVEL")
    bevel.width = 0.008
    bevel.segments = 2
    return obj


def skirt_layer(name, top_z, height, top_radius, bottom_radius, depth, phase, red_mat, black_mat, folds=20):
    rows, columns = 16, 160
    verts, faces = [], []
    for row in range(rows + 1):
        t = row / rows
        for col in range(columns):
            a = 2 * math.pi * col / columns
            fold = math.cos(a * folds + phase) * (0.018 + 0.025*t)
            radius = top_radius + (bottom_radius - top_radius) * (t**0.72) + fold
            z = top_z - height*t + math.sin(a*folds+phase) * 0.013 * t
            verts.append((math.cos(a)*radius, math.sin(a)*radius*depth, z))
    for row in range(rows):
        for col in range(columns):
            a = row*columns+col
            b = row*columns+(col+1)%columns
            c = (row+1)*columns+(col+1)%columns
            d = (row+1)*columns+col
            faces.append((a,b,c,d))
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    mesh.materials.append(red_mat); mesh.materials.append(black_mat)
    obj=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        sector=(poly.index % columns)//10
        # Let the black fabric dominate, with crimson panels as accents like
        # the approved reference rather than making the whole skirt neon red.
        poly.material_index = 0 if sector % 3 == 0 else 1
        poly.use_smooth = True
    solid=obj.modifiers.new("Fabric thickness","SOLIDIFY"); solid.thickness=0.025; solid.offset=0
    sub=obj.modifiers.new("Soft pleats","SUBSURF"); sub.levels=1; sub.render_levels=1
    # Double piping makes the layered construction read clearly at desktop size.
    edge_pts=[]
    for col in range(161):
        a=2*math.pi*col/160
        radius=bottom_radius+math.cos(a*folds+phase)*0.043
        z=top_z-height+math.sin(a*folds+phase)*0.013
        edge_pts.append((math.cos(a)*radius,math.sin(a)*radius*depth,z))
    curve(name+" hem scallop",edge_pts,0.021,black_mat,resolution=2)
    return obj


def bow(name, center, scale, red_mat, dark_mat, front=-1):
    x,y,z=center
    # Plush folded loops, one in front of the other to read as satin.
    for side in (-1,1):
        loop=sphere(f"{name} loop {side:+d}",(x+side*scale*0.13,y,z),(scale*0.22,scale*0.055,scale*0.13),red_mat,32,20)
        loop.rotation_euler[1]=side*0.34
        loop=sphere(f"{name} inner fold {side:+d}",(x+side*scale*0.13,y-front*scale*0.025,z),(scale*0.13,scale*0.035,scale*0.08),dark_mat,32,20)
        loop.rotation_euler[1]=side*0.34
    sphere(name+" knot",(x,y-front*scale*0.06,z),(scale*0.10,scale*0.07,scale*0.10),red_mat,32,20)
    for side in (-1,1):
        tapered_mesh(f"{name} tail {side:+d}",[
            (x+side*scale*0.06,y-front*scale*0.02,z-scale*0.03),
            (x+side*scale*0.13,y-front*scale*0.02,z-scale*0.18),
            (x+side*scale*0.20,y-front*scale*0.025,z-scale*0.32),
        ],[scale*0.065,scale*0.052,0.002],red_mat,sides=10,depth_ratio=0.25)


def ribbon_arc(name, angle_start, angle_end, upper, radius, y, red_mat, width):
    pts=[]
    for i in range(33):
        t=i/32
        a=angle_start+(angle_end-angle_start)*t
        z=1.91+0.23*math.cos(a)+(0.035 if upper else -0.025)
        x=math.sin(a)*radius
        yy=y-0.06*math.cos(a)
        pts.append((x,yy,z))
    return curve(name,pts,width,red_mat,resolution=2)


def setup_scene():
    # Keep the current UI workspace intact. read_factory_settings() resets
    # Blender's active editor and can interrupt this script when run in-console.
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.render.resolution_x=900; scene.render.resolution_y=900; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=True
    scene.render.resolution_percentage=100
    scene.render.image_settings.color_mode="RGBA"
    scene.view_settings.view_transform="Standard"
    scene.view_settings.look="Medium High Contrast"
    scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples=16
    scene.world=bpy.data.worlds.new("Soft transparent studio")
    scene.world.use_nodes=True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.22,0.18,0.22,1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value=0.18
    return scene


def lighting(scene):
    def area(name,loc,power,color,size,target=(0,0,1.1)):
        data=bpy.data.lights.new(name,"AREA"); data.energy=power; data.color=color; data.shape="DISK"; data.size=size
        obj=bpy.data.objects.new(name,data); scene.collection.objects.link(obj); obj.location=loc
        obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
    area("Key softbox",(-3.0,-4.5,4.5),310,(1.0,0.86,0.82),4.0)
    area("Cool fill",(3.4,-3.0,2.6),130,(0.78,0.82,1.0),3.5)
    area("Hair rim",(0.4,2.5,3.4),300,(1.0,0.48,0.52),3.0)


def make_face_patch(material):
    rows,cols=64,96
    xmin,xmax=-0.395,0.395
    zmin,zmax=1.125,2.015
    verts,faces,uvs=[],[],[]
    for j in range(rows+1):
        v=j/rows
        # A pointed chin and tapered hairline avoid the hard rectangular decal
        # edge in the first render.
        shape=0.10+0.90*(math.sin(math.pi*v)**0.55)
        for i in range(cols+1):
            u=i/cols
            x=(2*u-1)*(xmax-xmin)*0.5*shape
            z=zmin+(zmax-zmin)*v
            q=max(0.03,1-(x/0.445)**2-((z-1.62)/0.52)**2)
            y=-0.345*math.sqrt(q)-0.022
            verts.append((x,y,z))
            uvs.append((u,v))
    for j in range(rows):
        for i in range(cols):
            a=j*(cols+1)+i; b=a+1; c=b+cols+1; d=a+cols+1
            faces.append((a,b,c,d))
    mesh=bpy.data.meshes.new("Curved face texture shell")
    mesh.from_pydata(verts,[],faces); mesh.materials.append(material); mesh.update()
    obj=bpy.data.objects.new("Face | curved high-detail texture",mesh); bpy.context.collection.objects.link(obj)
    uv=mesh.uv_layers.new(name="Face UV")
    for loop in mesh.loops:
        uv.data[loop.index].uv=uvs[loop.vertex_index]
    for p in mesh.polygons: p.use_smooth=True
    return obj


def create_character(scene):
    skin=mat("Skin | warm porcelain",(0.98,0.79,0.69),0.8)
    hair=mat("Hair | charcoal espresso",(0.055,0.041,0.052),0.3)
    hair_hi=mat("Hair | muted mauve strands",(0.105,0.074,0.090),0.42)
    hair_glow=mat("Hair | narrow satin sheen",(0.16,0.112,0.125),0.5)
    red=mat("Satin | Kurumi crimson",(0.36,0.008,0.050),0.48)
    red_light=mat("Satin | lit crimson",(0.56,0.018,0.095),0.46)
    black=mat("Dress | near black",(0.035,0.025,0.045),0.72)
    lace=mat("Lace | soft black",(0.018,0.014,0.025),0.85)
    trim=mat("Trim | dark wine",(0.14,0.006,0.028),0.66)
    ivory=mat("Stockings | ivory",(0.96,0.84,0.79),0.75)
    gold=mat("Eye accent | antique gold",(0.73,0.36,0.055),0.32,0.25)
    face=mat("Face | approved heterochromia texture",(1,1,1),0.85,image=TEXTURES/"face.png",emission=0.08)
    # Use a gently lit texture; eye and linework stay crisp at pet scale.
    for node in face.node_tree.nodes:
        if node.type=="BSDF_PRINCIPLED":
            node.inputs["Roughness"].default_value=0.88

    # The short body and large head follow the existing desktop-pet silhouette.
    sphere("Head | rounded face volume",(0,0.015,1.62),(0.45,0.365,0.515),skin)
    sphere("Hair cap | rear mass",(0,0.075,1.70),(0.485,0.375,0.555),hair)
    make_face_patch(face)

    # Back hair and a few soft visible strand ridges establish real depth.
    for side in (-1,1):
        for k in range(3):
            x=side*(0.30+k*0.045)
            curve(f"Side hair ridge {side:+d}.{k}",[
                (x,0.015,1.98-k*0.025),
                (side*(0.43+k*0.025),-0.005,1.75-k*0.02),
                (side*(0.42+k*0.02),-0.025,1.47-k*0.025),
            ],0.018-k*0.002,hair_hi,[0.15,1.0,0.03])

    # Fine, curved grooves on the rear cap keep the back view from reading as
    # a single smooth helmet. Each groove follows the ellipsoid surface.
    def rear_surface_y(x,z):
        q=max(0.025,1-(x/0.485)**2-((z-1.70)/0.555)**2)
        return 0.075+0.375*math.sqrt(q)+0.012
    for i in range(-5,6):
        x=i*0.064
        path=[
            (x*0.36,rear_surface_y(x*0.36,2.12-abs(i)*0.006),2.12-abs(i)*0.006),
            (x*0.78,rear_surface_y(x*0.78,1.94),1.94),
            (x*1.05,rear_surface_y(x*1.05,1.68),1.68),
            (x*0.84,rear_surface_y(x*0.84,1.42),1.42),
        ]
        curve(f"Rear hair strand {i:+d}",path,0.013,hair_hi,[0.04,0.8,0.72,0.02],resolution=16)
        if i in (-4,-2,0,2,4):
            highlight=[(px+0.012,py+0.004,pz-0.015) for px,py,pz in path[1:]]
            curve(f"Rear hair satin glint {i:+d}",highlight,0.005,hair_glow,[0.04,0.8,0.02],resolution=12)

    # Individual tapered bangs; they overlap the forehead but leave both eyes clear.
    bang_specs=[
        ([-0.40,-0.30,-0.22],[1.91,1.78,1.60],0.065),
        ([-0.28,-0.20,-0.12],[1.98,1.81,1.64],0.070),
        ([-0.14,-0.07,0.015],[2.02,1.81,1.59],0.075),
        ([0.00,0.065,0.12],[2.03,1.81,1.65],0.074),
        ([0.14,0.22,0.27],[1.99,1.82,1.67],0.068),
        ([0.28,0.34,0.37],[1.92,1.77,1.61],0.058),
    ]
    for i,(xs,zs,width) in enumerate(bang_specs):
        pts=[(xs[k],-0.365-(0.02 if k==1 else 0),zs[k]) for k in range(3)]
        tapered_mesh(f"Bangs | sculpted lock {i+1:02d}",pts,[width,width*0.78,0.004],hair,sides=14,depth_ratio=0.42)
        if i in (1,3,4):
            curve(f"Bangs highlight {i+1:02d}",[(xs[0],-0.404,zs[0]-0.02),(xs[1],-0.414,zs[1]-0.07),(xs[2],-0.395,zs[2]+0.035)],0.008,hair_hi,[0.2,1.0,0.04])

    # Face-framing side locks, with tapered tips at the upper bodice.
    for side in (-1,1):
        tapered_mesh(f"Face frame | outer {side:+d}",[
            (side*0.38,-0.23,1.83),(side*0.46,-0.31,1.54),(side*0.43,-0.29,1.28),(side*0.28,-0.25,1.06)
        ],[0.10,0.105,0.085,0.006],hair,sides=14,depth_ratio=0.52)
        tapered_mesh(f"Face frame | inner {side:+d}",[
            (side*0.29,-0.31,1.89),(side*0.34,-0.37,1.63),(side*0.29,-0.35,1.41),(side*0.24,-0.31,1.26)
        ],[0.065,0.075,0.055,0.004],hair,sides=14,depth_ratio=0.45)

    # Long, layered twin tails: curved, tapered hair tubes instead of blunt blocks.
    for side in (-1,1):
        root=(side*0.42,0.09,1.82)
        sphere(f"Twin-tail root {side:+d}",root,(0.18,0.17,0.17),hair,40,24)
        paths=[
            [(side*0.44,0.08,1.82),(side*0.67,0.08,1.62),(side*0.82,0.06,1.31),(side*0.74,-0.02,1.00),(side*0.54,-0.05,0.84)],
            [(side*0.43,0.00,1.80),(side*0.62,-0.02,1.57),(side*0.71,-0.06,1.27),(side*0.62,-0.10,1.02),(side*0.45,-0.10,0.92)],
            [(side*0.48,0.15,1.81),(side*0.72,0.18,1.57),(side*0.88,0.10,1.30),(side*0.81,0.02,1.08),(side*0.62,-0.02,0.89)],
            [(side*0.42,0.16,1.78),(side*0.56,0.25,1.54),(side*0.66,0.21,1.27),(side*0.55,0.12,1.04),(side*0.37,0.02,0.94)],
        ]
        for j,path in enumerate(paths):
            width=[0.135,0.092,0.085,0.055][j]
            curve(f"Twin-tail {side:+d} | lock {j+1}",path,width,hair,[0.78,1.12,1.0,0.72,0.015],resolution=20)
            # Discrete, low-contrast grooves make the hair read as layered strands.
            if j in (0,2):
                offset=-side*0.028
                curve(f"Twin-tail sheen {side:+d}.{j}",[(x+offset,y-0.045,z+0.025) for x,y,z in path[:-1]],0.010,hair_hi,[0.08,0.8,0.75,0.08],resolution=20)

    # Gothic bonnet: a padded arch, lace lattice, ruffled edge, and symmetric bows.
    # A soft red velvet crown under the front band gives the bonnet the padded
    # silhouette in the approved sprite.
    sphere("Bonnet | padded velvet crown",(0,-0.27,2.085),(0.39,0.12,0.205),red,48,32)
    ribbon_arc("Bonnet | lower wine band",-1.18,1.18,False,0.50,-0.36,trim,0.075)
    ribbon_arc("Bonnet | crimson satin band",-1.14,1.14,True,0.51,-0.405,red,0.052)
    ribbon_arc("Bonnet | black upper piping",-1.10,1.10,True,0.54,-0.38,black,0.018)
    for i in range(11):
        a0=-1.07+i*0.194
        p1=(math.sin(a0)*0.47,-0.454,1.92+0.19*math.cos(a0))
        p2=(math.sin(a0+0.28)*0.51,-0.458,1.92+0.19*math.cos(a0+0.28))
        p3=(math.sin(a0+0.56)*0.55,-0.435,1.92+0.19*math.cos(a0+0.56))
        curve(f"Bonnet lattice / {i:02d}",[p1,p2,p3],0.011,trim,[0.65,1.0,0.65],resolution=8)
    for i in range(19):
        a=-1.12+i*(2.24/18)
        x=math.sin(a)*0.53; z=1.94+0.255*math.cos(a)
        sphere(f"Bonnet ruffle {i:02d}",(x,-0.382,z+0.025),(0.043,0.033,0.052),red_light,24,16)
    for side in (-1,1):
        bow(f"Hair ribbon {side:+d}",(side*0.49,-0.37,1.84),0.70,red,trim)

    # Short neck, lace collar and off-shoulder bodice match the compact pet outfit.
    sphere("Neck",(0,-0.005,1.205),(0.16,0.15,0.18),skin,40,24)
    for i in range(24):
        a=2*math.pi*i/24
        sphere(f"Collar scallop {i:02d}",(0.20*math.cos(a),-0.02+0.15*math.sin(a),1.235),(0.034,0.025,0.034),lace,20,12)
    curve("Collar red piping",[(0.20*math.cos(a),-0.02+0.158*math.sin(a),1.20+0.04*math.cos(a)) for a in [2*math.pi*i/64 for i in range(65)]],0.014,red)
    sphere("Bodice | short rounded torso",(0,0.005,0.96),(0.30,0.215,0.36),black)
    # Red chest panels and scalloped lace keep the tiny bodice readable at
    # desktop-pet scale.
    for side in (-1,1):
        cup=sphere(f"Bodice | crimson chest panel {side:+d}",(side*0.12,-0.202,1.105),(0.095,0.014,0.058),red,36,24)
        cup.rotation_euler[1]=side*-0.10
    for i in range(17):
        a=math.pi+(math.pi*i/16)
        sphere(f"Bodice neckline lace {i:02d}",(0.245*math.cos(a),-0.165,1.12+0.045*math.sin(a)),(0.023,0.018,0.028),lace,16,10)
    # A fitted crimson corset overlay shaped to the short torso.
    torso_verts=[]; torso_faces=[]; rows=18; cols=48
    for row in range(rows+1):
        t=row/rows; z=1.13-0.34*t
        rx=0.23-0.055*t; ry=0.18-0.035*t
        for col in range(cols):
            a=2*math.pi*col/cols
            torso_verts.append((math.cos(a)*rx,0.005+math.sin(a)*ry,z))
    for row in range(rows):
        for col in range(cols):
            a=row*cols+col;b=row*cols+(col+1)%cols;c=(row+1)*cols+(col+1)%cols;d=(row+1)*cols+col
            torso_faces.append((a,b,c,d))
    mesh=bpy.data.meshes.new("Corset tailored shell");mesh.from_pydata(torso_verts,[],torso_faces);mesh.materials.append(red);mesh.update()
    corset=bpy.data.objects.new("Corset | crimson fitted shell",mesh);bpy.context.collection.objects.link(corset)
    for p in mesh.polygons:p.use_smooth=True
    solid=corset.modifiers.new("Corset thickness","SOLIDIFY");solid.thickness=0.014
    # Central black panel and fine gold/red lacing follow the body curvature.
    sphere("Corset center panel",(0,-0.201,0.95),(0.095,0.025,0.23),black,40,24)
    for i in range(5):
        z=0.80+i*0.067
        curve(f"Corset lacing cross {i}",[(-0.067,-0.231,z+0.024),(0.067,-0.231,z-0.024)],0.008,gold,[0.75,0.75],resolution=2)
    curve("Corset center seam",[(0,-0.235,0.78),(0,-0.235,1.12)],0.009,trim)

    # Puffy detached sleeves and little hands.
    for side in (-1,1):
        sphere(f"Shoulder skin {side:+d}",(side*0.29,-0.01,1.11),(0.13,0.14,0.12),skin)
        sphere(f"Sleeve puff {side:+d}",(side*0.34,-0.01,0.96),(0.17,0.17,0.22),black)
        sphere(f"Sleeve red cuff {side:+d}",(side*0.39,-0.015,0.81),(0.13,0.14,0.07),trim)
        for i in range(9):
            a=2*math.pi*i/9
            sphere(f"Sleeve lace {side:+d}.{i}",(side*0.39+0.13*math.cos(a),-0.015+0.14*math.sin(a),0.81),(0.028,0.021,0.034),lace,16,10)
        sphere(f"Forearm {side:+d}",(side*0.39,-0.06,0.70),(0.078,0.085,0.14),skin)
        sphere(f"Hand {side:+d}",(side*0.39,-0.09,0.59),(0.087,0.075,0.080),skin,32,20)
        bow(f"Sleeve bow {side:+d}",(side*0.37,-0.175,0.96),0.30,red,trim)

    bow("Waist bow",(0,-0.39,0.875),0.46,red_light,trim)

    # Broad layered skirt: short waist, expanding hem, alternating red/black panels.
    skirt_layer("Skirt | upper pleated tier",0.87,0.19,0.245,0.48,0.74,0.0,red,black,18)
    skirt_layer("Skirt | middle bell tier",0.70,0.20,0.43,0.62,0.76,0.35,red_light,black,20)
    skirt_layer("Skirt | lower wide tier",0.52,0.20,0.58,0.73,0.78,0.12,red,black,22)
    skirt_layer("Skirt | lace underskirt",0.38,0.10,0.66,0.78,0.79,0.4,black,lace,24)
    # Small red bows and piped seams make the tiers read as sewn clothing.
    for side in (-1,1):
        bow(f"Skirt side bow {side:+d}",(side*0.48,-0.285,0.67),0.34,red,trim)
    for z,radius,depth in [(0.70,0.50,0.76),(0.52,0.66,0.78)]:
        curve(f"Skirt seam piping {z}",[(math.cos(a)*radius,math.sin(a)*radius*depth,z) for a in [2*math.pi*i/128 for i in range(129)]],0.010,trim,resolution=2)

    # Barely visible short legs, ivory socks, black-red Mary Janes.
    for side in (-1,1):
        x=side*0.17
        sphere(f"Leg {side:+d}",(x,0.01,0.265),(0.09,0.095,0.15),skin,32,20)
        sphere(f"Sock cuff {side:+d}",(x,0.0,0.365),(0.10,0.103,0.055),ivory,32,16)
        for i in range(11):
            a=2*math.pi*i/11
            sphere(f"Sock scallop {side:+d}.{i}",(x+0.10*math.cos(a),0.10*math.sin(a),0.37),(0.024,0.021,0.024),lace,16,10)
        shoe=sphere(f"Mary Jane {side:+d}",(x,-0.05,0.12),(0.145,0.20,0.115),black,40,24)
        sphere(f"Shoe toe red {side:+d}",(x,-0.205,0.15),(0.09,0.025,0.06),trim,28,16)
        bow(f"Shoe bow {side:+d}",(x,-0.226,0.17),0.23,red_light,trim)

    # Small hardware on the corset and headband.
    for side in (-1,1):
        sphere(f"Corset stud {side:+d}",(side*0.16,-0.183,1.08),(0.025,0.018,0.025),gold,24,16)

    # Group geometry while keeping separate descriptive objects for later rigging.
    root=bpy.data.objects.new("Kurumi Desktop Pet | V3 model root",None)
    scene.collection.objects.link(root)
    root.empty_display_type="PLAIN_AXES";root.empty_display_size=0.12
    for obj in list(scene.objects):
        if obj != root and obj.type not in {"CAMERA","LIGHT"}:
            obj.parent=root
    return root


def camera_for(scene, name, loc, target, size, path):
    data=bpy.data.cameras.new(name); data.type="ORTHO"; data.ortho_scale=size
    cam=bpy.data.objects.new(name,data);scene.collection.objects.link(cam);cam.location=loc
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler();scene.camera=cam
    scene.render.filepath=str(path)
    return cam


def main():
    scene=setup_scene()
    create_character(scene)
    lighting(scene)
    target=(0,0,1.12)
    views=[
      ("front.png",(0,-7,1.14),2.45),
      ("quarter.png",(3.8,-6.3,1.22),2.58),
      ("side.png",(7,0,1.15),2.60),
      ("back.png",(0,7,1.15),2.60),
    ]
    # Save the editable scene and portable mesh before rendering previews so a
    # render-device hiccup never loses the actual model.
    camera_for(scene,"Front modeling camera",(0,-7,1.14),target,2.45,OUT/"front.png")
    scene.render.filepath=str(OUT/"front.png")
    for image in bpy.data.images:
        if image.source=="FILE":
            try:image.pack()
            except RuntimeError:pass
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"kurumi-v3.blend"))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=str(OUT/"kurumi-v3.glb"),export_format="GLB",export_apply=True)
    bpy.ops.wm.usd_export(filepath=str(OUT/"kurumi-v3.usdz"),selected_objects_only=True,
        export_lights=False,export_cameras=False,export_meshes=True,export_curves=True,
        export_materials=True,export_textures=True)
    for filename,loc,size in views:
        camera_for(scene,filename,loc,target,size,OUT/filename)
        bpy.ops.render.render(write_still=True)
    # Return the saved editing view to the front orthographic camera.
    camera_for(scene,"Front modeling camera",(0,-7,1.14),target,2.45,OUT/"front.png")
    scene.render.filepath=str(OUT/"front.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"kurumi-v3.blend"))
    print(f"Saved blend, GLB, USDZ and four views under {OUT}")


if __name__=="__main__":
    main()
