"""Mesh helpers extracted from this project's earlier modeling study.

No external base mesh or third-party modeling script is included.
This module has no scene-building side effects when loaded.
"""
import bpy, bmesh
from mathutils import Vector

def mesh(name,vs,fs,mat,sub=0,thick=0):
    d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();d.materials.append(mat)
    bm=bmesh.new();bm.from_mesh(d);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(d);bm.free()
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
    for p in d.polygons:p.use_smooth=True
    if sub:
        s=o.modifiers.new('Smooth tailored surface','SUBSURF');s.levels=sub;s.render_levels=sub
    if thick:
        s=o.modifiers.new('Cloth thickness','SOLIDIFY');s.thickness=thick
    return o

def uvball(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o

def line(name,pts,r,mat,radii=None):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=12;d.bevel_depth=r;d.bevel_resolution=3
    s=d.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
    for i,(bp,p) in enumerate(zip(s.bezier_points,pts)):
        bp.co=p;bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
        if radii:bp.radius=radii[i]
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(mat);return o

def catmull(ps,ws,n=12):
    ps=[Vector(p) for p in ps];pts=[];width=[]
    for j in range(len(ps)-1):
        a,b,c,d=ps[max(0,j-1)],ps[j],ps[j+1],ps[min(j+2,len(ps)-1)]
        for k in range(n):
            t=k/n
            pts.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
            wa,wb,wc,wd=ws[max(0,j-1)],ws[j],ws[j+1],ws[min(j+2,len(ws)-1)]
            width.append(max(.001,.5*(2*wb+(-wa+wc)*t+(2*wa-5*wb+4*wc-wd)*t*t+(-wa+3*wb-3*wc+wd)*t*t*t)))
    return pts+[ps[-1]],width+[ws[-1]]

def add_ink_contours(scene):
    """Thin inverted hulls keep the silhouette readable at desktop-pet scale."""
    ink=bpy.data.materials.new('Ink | charcoal contour');ink.use_nodes=True;ink.use_backface_culling=True
    nodes=ink.node_tree.nodes;nodes.clear()
    surface=nodes.new('ShaderNodeEmission');surface.inputs[0].default_value=(.007,.0045,.006,1)
    output=nodes.new('ShaderNodeOutputMaterial');ink.node_tree.links.new(surface.outputs[0],output.inputs['Surface'])
    bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get()
    prefixes=('Head |','Hair |','Bangs |','Twin-tail |','Bonnet |','Dress |','Bodice |','Sleeve |','Hair tie','Waist |')
    originals=[obj for obj in scene.objects if obj.type=='MESH' and obj.name.startswith(prefixes)]
    for original in originals:
        data=bpy.data.meshes.new_from_object(original.evaluated_get(graph))
        data.transform(original.matrix_world)
        bm=bmesh.new();bm.from_mesh(data);bm.normal_update()
        width=.00165 if original.name.startswith(('Head |','Hair |','Bangs |','Twin-tail |')) else .0011
        for vertex in bm.verts:vertex.co+=vertex.normal*width
        bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free();data.update()
        data.materials.clear();data.materials.append(ink)
        for poly in data.polygons:poly.material_index=0;poly.use_smooth=True
        obj=bpy.data.objects.new('Ink | '+original.name,data);scene.collection.objects.link(obj)
