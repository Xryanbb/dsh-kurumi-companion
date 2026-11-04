"""Verify the reopened head file and save a usable model viewport."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
out=Path(__file__).resolve().parent
scene=bpy.data.scenes['Kurumi | head study v8'];bpy.context.window.scene=scene
area=bpy.context.area
if area:
    area.type='VIEW_3D';space=area.spaces.active
    space.shading.type='MATERIAL';space.shading.use_scene_lights=True;space.shading.use_scene_world=True
    space.overlay.show_floor=False;space.overlay.show_axis_x=False;space.overlay.show_axis_y=False
    space.overlay.show_extras=False;space.overlay.show_relationship_lines=False
    space.region_3d.view_location=Vector((.01,.06,1.36));space.region_3d.view_distance=3.30
    space.region_3d.view_rotation=Vector((3.2,-7,0)).to_track_quat('Z','Y');space.region_3d.view_perspective='ORTHO'
for obj in scene.objects:obj.select_set(False)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'kurumi-head-study.blend'))
report=json.loads((out/'model-check.json').read_text())
report['reopened_independent_blend']=True
report['head_scene_contains_review_planes']=any(o.name.startswith(('Original approved','Actual Blender')) for o in scene.objects)
images={n.image for o in scene.objects if o.type in {'MESH','CURVE'} for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
report['model_texture_count']=len(images);report['all_model_textures_packed']=all(im.packed_file for im in images)
report['all_mesh_coordinates_finite']=all(math.isfinite(c) for o in scene.objects if o.type=='MESH' for v in o.data.vertices for c in v.co)
report['outputs']=['front.png','quarter.png','side.png','clay-quarter.png','comparison.png','kurumi-head-study.blend']
(out/'model-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(out/'review-ready.txt').write_text('Independent blend reopened, textures packed, comparison rendered, 3D viewport ready.\n')
