"""Review board of unretouched actual render outputs and original artwork.
These planes exist only in the comparison scene, never in the head model.
"""
import bpy, math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
SOURCE=OUT.parents[2]/'extras/kurumi-animation/reference/idle-approved.png'

def compare():
    main=bpy.data.scenes['Kurumi | head study v8'];name='Kurumi | v8 head comparison'
    if name in bpy.data.scenes:
        old=bpy.data.scenes[name]
        for o in list(old.objects):
            if len(o.users_scene)==1:bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.scenes.remove(old)
    s=bpy.data.scenes.new(name);s.world=bpy.data.worlds.new('Head comparison background');s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.034,.041,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value=1
    s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=32
    s.render.resolution_x=2100;s.render.resolution_y=600;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.film_transparent=False
    s.view_settings.view_transform='Standard';s.view_settings.look='None'
    x0,x1,z0,z1=-.90,.90,1.10,2.22
    def panel(name,path,centre,uvs):
        data=bpy.data.meshes.new(name);data.from_pydata([(centre+x0,0,z0),(centre+x1,0,z0),(centre+x1,0,z1),(centre+x0,0,z1)],[],[(0,1,2,3)])
        uv=data.uv_layers.new(name='Review crop')
        for loop in data.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
        mat=bpy.data.materials.new(name);mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();l=mat.node_tree.links
        tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=False);tex.image.pack()
        e=n.new('ShaderNodeEmission');l.new(tex.outputs['Color'],e.inputs[0]);t=n.new('ShaderNodeBsdfTransparent')
        mix=n.new('ShaderNodeMixShader');l.new(tex.outputs['Alpha'],mix.inputs[0]);l.new(t.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2])
        o=n.new('ShaderNodeOutputMaterial');l.new(mix.outputs[0],o.inputs[0]);mat.surface_render_method='DITHERED'
        data.materials.append(mat);obj=bpy.data.objects.new(name,data);s.collection.objects.link(obj)
    def refuv(x,z):return ((697+x*433)/1374,1-(1150-z*433)/1145)
    def renderuv(x,z):return (.5+(x-.01)/2.24,.5+(z-1.36)/2.24)
    corners=[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
    panel('Original approved 2D',SOURCE,-1.92,[refuv(*p) for p in corners])
    panel('Actual Blender front render',OUT/'front.png',0,[renderuv(*p) for p in corners])
    panel('Actual Blender quarter render',OUT/'quarter.png',1.92,[renderuv(*p) for p in corners])
    lab=bpy.data.materials.new('Review labels');lab.use_nodes=True;n=lab.node_tree.nodes;e=n.new('ShaderNodeEmission');e.inputs[0].default_value=(.65,.61,.60,1);lab.node_tree.links.new(e.outputs[0],n.get('Material Output').inputs[0])
    for x,text in [(-1.92,'APPROVED 2D'),(0,'3D HEAD / FRONT'),(1.92,'3D HEAD / QUARTER')]:
        f=bpy.data.curves.new(text,'FONT');f.body=text;f.align_x='CENTER';f.size=.074;f.materials.append(lab)
        obj=bpy.data.objects.new(text,f);s.collection.objects.link(obj);obj.location=(x,-.01,1.00);obj.rotation_euler=(math.pi/2,0,0)
    cd=bpy.data.cameras.new('Head comparison camera');cd.type='ORTHO';cd.ortho_scale=5.80
    cam=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(cam);target=Vector((0,0,1.61));cam.location=target+Vector((0,-8,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
    s.render.filepath=str(OUT/'comparison.png');bpy.ops.render.render(write_still=True,scene=s.name)
    bpy.data.libraries.write(str(OUT/'kurumi-head-study.blend'),{main,s},fake_user=True,compress=True)

if __name__=='__main__':compare()
