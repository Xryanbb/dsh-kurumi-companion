"""Editable, full-volume head study. Review model only; no desktop deployment.

The approved illustration supplies proportions for a CLOSED skull and separate
CLOSED hair locks. An isolated facial atlas and dedicated painted hair albedo
are mapped onto those meshes. This is an unapproved modeling/texture study.
"""
import bpy, bmesh, math, runpy, json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
BASE=OUT.parents[2]
REFERENCE=BASE/'extras/kurumi-animation/reference/idle-approved.png'
H=runpy.run_path(str(OUT/'mesh_helpers.py'))
mesh=H['mesh']; line=H['line']; uvball=H['uvball']; catmull=H['catmull']
PI=math.pi
CX=697.; ZBASE=1150.; SCALE=433.

def pxy(x,y,depth):return ((x-CX)/SCALE,depth,(ZBASE-y)/SCALE)

def plain(name,color,rough=.8):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.18
    return m

def mathnode(nodes,links,op,a,b=None):
    n=nodes.new('ShaderNodeMath');n.operation=op
    for i,arg in enumerate([a,b]):
        if arg is None:continue
        if isinstance(arg,(int,float)):n.inputs[i].default_value=arg
        else:links.new(arg,n.inputs[i])
    return n.outputs[0]

def paint_material(name,base,image,kind):
    """Artwork is used only on front-facing geometry; retain volume at all angles."""
    m=plain(name,base);n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial')
    uv=n.new('ShaderNodeUVMap');uv.uv_map='StrandUV' if kind=='hair' else 'FaceUV'
    tex=n.new('ShaderNodeTexImage');tex.image=image;tex.extension='EXTEND';l.new(uv.outputs[0],tex.inputs[0])
    geom=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ')
    local=n.new('ShaderNodeVectorTransform');local.vector_type='NORMAL';local.convert_from='WORLD';local.convert_to='OBJECT'
    l.new(geom.outputs['Normal'],local.inputs[0]);l.new(local.outputs[0],sep.inputs[0])
    front=mathnode(n,l,'MULTIPLY',sep.outputs['Y'],-1)
    fade=n.new('ShaderNodeMapRange');fade.clamp=True
    fade.inputs['From Min'].default_value=.25;fade.inputs['From Max'].default_value=.75
    l.new(front,fade.inputs[0])
    mask=mathnode(n,l,'MULTIPLY',fade.outputs[0],tex.outputs['Alpha'])
    color=n.new('ShaderNodeMixRGB');color.inputs[1].default_value=(*base,1)
    if kind=='hair':
        # Dedicated image-generated albedo contains hair fibres only, so no
        # original bows, faces or other locks are projected onto the geometry.
        color.inputs[0].default_value=1
        gain=n.new('ShaderNodeMixRGB');gain.blend_type='MULTIPLY';gain.inputs[0].default_value=1
        gain.inputs[2].default_value=(1.25,1.25,1.25,1);l.new(tex.outputs['Color'],gain.inputs[1])
        l.new(gain.outputs[0],color.inputs[2])
    else:
        l.new(mask,color.inputs[0]);l.new(tex.outputs['Color'],color.inputs[2])
    diffuse=n.new('ShaderNodeBsdfDiffuse');diffuse.inputs['Color'].default_value=(.8,.8,.8,1)
    shade=n.new('ShaderNodeShaderToRGB');l.new(diffuse.outputs[0],shade.inputs[0])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE'
    ramp.color_ramp.elements[0].position=.05;ramp.color_ramp.elements[0].color=(.67,.65,.67,1)
    ramp.color_ramp.elements[1].position=.75;ramp.color_ramp.elements[1].color=(1.08,1.06,1.07,1)
    if kind=='skin':
        ramp.color_ramp.elements[0].color=(.83,.80,.80,1)
        ramp.color_ramp.elements[1].color=(1.,1.,1.,1)
    l.new(shade.outputs[0],ramp.inputs[0])
    multiply=n.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
    l.new(color.outputs[0],multiply.inputs[1]);l.new(ramp.outputs[0],multiply.inputs[2])
    emission=n.new('ShaderNodeEmission');l.new(multiply.outputs[0],emission.inputs[0]);l.new(emission.outputs[0],out.inputs['Surface'])
    return m

def projection(obj):
    uv=obj.data.uv_layers.get('ArtworkProjection') or obj.data.uv_layers.new(name='ArtworkProjection')
    for loop in obj.data.loops:
        p=obj.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv=((p.x*SCALE+CX)/1374,1-(ZBASE-p.z*SCALE)/1145)
    return obj

def strand(name,path,widths,mat,depth=.50,twist=0):
    """Closed lens-section swept mesh, with true thickness and individual curls."""
    points=[pxy(x,z,y) for x,z,y in path]
    ps,ws=catmull(points,[w/SCALE for w in widths],10)
    vs=[];fs=[];uvs=[];sides=16
    for i,(p,w) in enumerate(zip(ps,ws)):
        t=(ps[min(i+1,len(ps)-1)]-ps[max(i-1,0)]).normalized()
        a=Vector((-t.z,0,t.x)).normalized()
        if a.length<.1:a=Vector((1,0,0))
        d=t.cross(a).normalized()
        if d.y>0:d=-d
        roll=twist*math.sin(PI*i/(len(ps)-1))
        a,d=a*math.cos(roll)+d*math.sin(roll),-a*math.sin(roll)+d*math.cos(roll)
        for j in range(sides):
            angle=2*PI*j/sides
            across=math.cos(angle)
            thick=math.copysign((1-abs(across)**1.6)**.75,math.sin(angle))
            taper=1
            if name.startswith('Bangs |'):
                progress=i/(len(ps)-1);taper=.5+.5*math.sin(PI*progress)**.5
            q=p+a*max(.0006,w)*across+d*(max(.0006,w)*depth*thick*taper)
            vs.append(tuple(q));uvs.append((j/sides,1-i/(len(ps)-1)))
    for i in range(len(ps)-1):
        for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    fs.extend([tuple(range(sides-1,-1,-1)),tuple((len(ps)-1)*sides+j for j in range(sides))])
    obj=mesh(name,vs,fs,mat,1);projection(obj)
    uv=obj.data.uv_layers.new(name='StrandUV')
    for loop in obj.data.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
    for poly in obj.data.polygons:
        indices=[obj.data.loops[k].vertex_index%sides for k in poly.loop_indices]
        if 0 in indices and sides-1 in indices:
            for k in poly.loop_indices:
                if obj.data.loops[k].vertex_index%sides==0:uv.data[k].uv.x=1
    return obj

def skull(face,skin):
    # Compact cheek and jaw; a slanted facial plane matches the approved eye line.
    rows=[(298,2,.0,.01),(312,75,.075,.13),(345,133,.16,.25),(395,162,.23,.33),
          (450,176,.265,.36),(510,178,.28,.35),(553,173,.278,.32),
          (584,162,.288,.27),(611,145,.285,.22),(634,115,.265,.15),
          (648,70,.226,.09),(653,2,.199,.01)]
    rows=list(reversed([(pxy(0,p,0)[2],r/SCALE,f,b) for p,r,f,b in rows]))
    def at(z,k):
        for j in range(len(rows)-1):
            if rows[j][0]<=z<=rows[j+1][0]:
                t=(z-rows[j][0])/(rows[j+1][0]-rows[j][0])
                a,b,c,d=[rows[max(0,min(len(rows)-1,q))][k] for q in (j-1,j,j+1,j+2)]
                return .5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
        return rows[-1][k]
    vs=[];fs=[];nr=90;nc=128
    z0,z1=rows[0][0],rows[-1][0]
    for i in range(nr+1):
        z=z0+(z1-z0)*i/nr;rx=at(z,1)
        for j in range(nc):
            angle=2*PI*j/nc;c=math.cos(angle);x=rx*math.sin(angle)
            y=-at(z,2)*c**.55 if c>=0 else at(z,3)*(-c)**.95
            if c>0:
                nose=.015*math.exp(-((x+.01)/.031)**2-((z-1.285)/.034)**2)
                lips=.009*math.exp(-((x-.015)/.065)**2-((z-1.215)/.016)**2)
                eye=.009*sum(math.exp(-((x-xc)/.074)**2-((z-1.345)/.05)**2) for xc in [-.16,.19])
                y+=eye-nose-lips
            vs.append((x+.012,y,z+.126*x))
    for i in range(nr):
        for j in range(nc):fs.append((i*nc+j,i*nc+(j+1)%nc,(i+1)*nc+(j+1)%nc,(i+1)*nc+j))
    fs.extend([tuple(range(nc-1,-1,-1)),tuple(nr*nc+j for j in range(nc))])
    o=projection(mesh('Head | closed sculpted profile',vs,fs,face,1))
    uv=o.data.uv_layers.new(name='FaceUV')
    for loop in o.data.loops:
        p=o.data.vertices[loop.vertex_index].co
        zz=p.z-.126*(p.x-.012)
        if zz>=1.26:v=.34+(zz-1.26)/.84
        elif zz>=1.213:v=.228+(zz-1.213)*(.112/.047)
        else:v=.228+(zz-1.213)*(.228/.093)
        uv.data[loop.index].uv=(.5+(p.x-.014)/.78,v)
    # Small modeled ears, hidden partially under the side locks.
    for s in [-1,1]:
        uvball('Ear | '+str(s),(s*.39,.005,1.36+s*.035),(.046,.033,.070),skin)
    return o,at

def hair_crown(hair,at):
    vs=[];fs=[];nr=38;nc=104
    for i in range(nr+1):
        t=i/nr
        for j in range(nc):
            a=2*PI*j/nc;c=math.cos(a)
            end=1.15+.39*max(0,c)**.7
            z=1.975-(1.975-end)*t
            sz=max(1.149,min(1.965,z-.018))
            pad=.016+.008*math.sin(a*16)**2
            x=(at(sz,1)+pad)*math.sin(a)
            y=-(at(sz,2)+pad)*c**.55 if c>=0 else (at(sz,3)+pad)*(-c)**.95
            vs.append((x+.012,y,z+.11*x))
    for i in range(nr):
        for j in range(nc):fs.append((i*nc+j,i*nc+(j+1)%nc,(i+1)*nc+(j+1)%nc,(i+1)*nc+j))
    o=projection(mesh('Hair | crown volume',vs,fs,hair,1,.008))
    uv=o.data.uv_layers.new(name='StrandUV')
    for loop in o.data.loops:
        idx=loop.vertex_index;uv.data[loop.index].uv=(idx%nc/nc,1-idx//nc/nr)
    for poly in o.data.polygons:
        indices=[o.data.loops[k].vertex_index%nc for k in poly.loop_indices]
        if 0 in indices and nc-1 in indices:
            for k in poly.loop_indices:
                if o.data.loops[k].vertex_index%nc==0:uv.data[k].uv.x=1

def hair_locks(hair):
    # Pixel-space centre lines reproduce the non-symmetric silhouette. Widths are
    # half-widths; depth is independent, so turning the view reveals true volumes.
    bangs=[
      ('left outer',[(567,364,-.12),(541,439,-.28),(531,517,-.30),(507,591,-.22)],[17,24,17,.3]),
      ('left long',[(611,353,-.14),(582,427,-.29),(567,499,-.32),(572,554,-.34)],[22,30,20,.3]),
      ('left division',[(620,350,-.14),(603,418,-.31),(600,489,-.34),(623,553,-.35)],[12,17,16,.3]),
      ('centre sweep',[(651,340,-.12),(643,414,-.315),(655,487,-.355),(690,545,-.35),(730,574,-.32)],[20,39,31,18,.3]),
      ('centre thin',[(665,347,-.17),(661,424,-.34),(680,494,-.376),(707,550,-.36),(734,576,-.32)],[10,13,12,9,.3]),
      ('right inner',[(699,343,-.12),(723,418,-.31),(754,489,-.35),(802,539,-.31),(846,560,-.22)],[21,33,28,16,.3]),
      ('right outer',[(757,363,-.13),(809,430,-.28),(841,501,-.27),(857,557,-.19)],[22,27,19,.3]),
      ('left tip',[(582,403,-.29),(556,476,-.34),(558,536,-.35),(548,568,-.32)],[8,12,9,.2]),
    ]
    for name,path,width in bangs:
        # Roots sink into the crown instead of sitting on it as raised leaves.
        path[0]=(path[0][0],path[0][1]-.5,path[0][2]+.045)
        strand('Bangs | '+name,path,width,hair,.23)
    cheeks=[
      ('left short',[(542,441,-.20),(530,518,-.28),(548,588,-.30),(575,617,-.31),(606,634,-.27)],[22,23,20,11,.4]),
      ('right short',[(826,405,-.18),(852,484,-.25),(851,564,-.26),(817,610,-.29),(800,622,-.26)],[20,23,20,12,.4]),
      ('left long',[(528,452,-.10),(515,550,-.19),(532,630,-.18),(569,692,-.15),(623,718,-.10)],[18,24,19,12,.4]),
      ('right long',[(859,463,-.09),(863,555,-.17),(849,622,-.18),(824,677,-.17),(798,705,-.12)],[16,24,21,12,.4]),
      ('left loose',[(516,467,-.02),(506,564,-.09),(515,649,-.08),(543,704,-.07),(564,713,-.07)],[8,13,10,6,.3]),
      ('right loose',[(874,475,-.01),(880,568,-.09),(871,631,-.07),(845,675,-.05)],[7,11,8,.3])]
    for name,path,width in cheeks:strand('Hair | cheek '+name,path,width,hair,.50)
    # Each tail has a narrow root, separated inner curls, a longer outer curl,
    # and fine flyaway loops. Stagger their Y positions to avoid stacked leaves.
    tails=[
      ('L core',[(494,431,.13),(466,326,.19),(430,398,.18),(409,499,.15),(415,602,.06),(440,692,-.01),(477,741,-.04),(519,751,-.02)],[12,25,30,32,29,22,12,.3],.60),
      ('L curl one',[(490,426,.18),(468,330,.24),(427,445,.25),(398,574,.19),(388,690,.12),(408,763,.04),(445,794,.01),(469,790,.00),(477,768,.01)],[13,21,28,31,26,21,14,7,.3],.70),
      ('L curl two',[(488,425,.23),(461,329,.31),(420,454,.34),(395,617,.31),(366,744,.23),(370,814,.16),(404,860,.11),(444,857,.08),(460,840,.06)],[12,19,25,27,25,20,13,6,.3],.65),
      ('L lower',[(486,429,.28),(467,338,.36),(435,474,.42),(400,640,.39),(356,768,.34),(356,838,.25),(379,882,.19),(408,896,.16),(419,884,.13),(405,866,.12)],[12,17,23,24,21,18,14,9,5,.3],.70),
      ('L outer',[(486,430,.31),(461,316,.32),(421,365,.30),(380,460,.25),(363,521,.21),(380,552,.18),(405,543,.16)],[12,17,19,13,9,5,.3],.55),
      ('L flyaway',[(473,352,.27),(414,460,.24),(357,575,.14),(330,651,.10),(345,679,.07),(370,672,.04),(377,653,.01)],[3,7,8,6,4,2,.2],.65),
      ('L thread',[(418,599,.30),(366,708,.23),(326,757,.21),(313,803,.20),(337,827,.16)],[3,5,5,3,.2],.6),
      ('R core',[(880,420,.14),(900,308,.21),(931,376,.20),(954,492,.15),(950,611,.06),(920,692,-.01),(885,728,-.03),(854,735,-.02)],[12,26,31,33,29,21,11,.3],.62),
      ('R curl one',[(879,424,.20),(895,309,.27),(946,429,.29),(980,552,.22),(983,671,.14),(959,754,.06),(920,790,.03),(895,788,.01),(886,773,.02)],[12,23,29,31,27,22,13,6,.3],.68),
      ('R curl two',[(881,422,.24),(899,318,.33),(952,445,.38),(982,600,.33),(1019,746,.26),(1019,815,.18),(987,853,.12),(952,851,.10),(944,833,.08)],[13,23,27,29,27,22,14,6,.3],.7),
      ('R lower',[(882,425,.30),(902,324,.37),(954,472,.44),(994,647,.40),(1049,775,.33),(1065,837,.27),(1053,883,.20),(1030,900,.16),(1019,887,.14),(1031,870,.13)],[12,20,25,27,24,20,14,8,5,.3],.70),
      ('R outer',[(884,422,.32),(904,300,.33),(945,357,.31),(1004,462,.25),(1031,548,.22),(1027,589,.18),(1008,605,.16)],[12,18,18,12,8,5,.3],.55),
      ('R flyaway',[(943,403,.30),(1004,529,.23),(1052,625,.15),(1062,673,.10),(1039,687,.07),(1026,671,.03)],[3,6,7,5,3,.2],.65),
      ('R thread',[(985,612,.31),(1038,706,.26),(1085,770,.22),(1100,816,.17),(1078,846,.12)],[3,6,5,3,.2],.6),
    ]
    for name,path,width,dep in tails:
        if 'flyaway' not in name and 'thread' not in name:
            x=514 if name[0]=='L' else 869
            path.insert(0,(x,437,.085));width.insert(0,8)
        strand('Twin-tail | '+name,path,width,hair,dep,twist=.12 if name[0]=='L' else -.12)

def render(out=OUT):
    # Preserve the user's preceding Blender session once, before creating study.
    backup=OUT/'before-v8-session.blend'
    if not backup.exists():bpy.ops.wm.save_as_mainfile(filepath=str(backup),copy=True)
    name='Kurumi | head study v8'
    if name in bpy.data.scenes:
        old=bpy.data.scenes[name]
        for o in list(old.objects):
            if len(o.users_scene)==1:bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.scenes.remove(old)
    scene=bpy.data.scenes.new(name);bpy.context.window.scene=scene
    scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=64
    scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
    scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast'
    scene.world=bpy.data.worlds.new('Head study | studio');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.4,.4,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    ref=bpy.data.images.load(str(REFERENCE),check_existing=True);ref.pack()
    hairtex=bpy.data.images.load(str(OUT/'hair-albedo.png'),check_existing=True);hairtex.pack()
    facetex=bpy.data.images.load(str(BASE/'assets/kurumi3d/v2/face.png'),check_existing=True);facetex.pack()
    hair=paint_material('Hair | painted strand study',(.033,.024,.028),hairtex,'hair')
    face=paint_material('Face | calibrated isolated face artwork',(.92,.76,.65),facetex,'skin')
    skin=plain('Skin | warm ivory',(.93,.76,.66),.95)
    red=plain('Cloth | dark carmine',(.36,.018,.03),.8)
    black=plain('Cloth | charcoal',(.014,.008,.012),.85)
    head,profile=skull(face,skin);hair_crown(hair,profile);hair_locks(hair)
    bonnet=OUT/'bonnet.py'
    if bonnet.exists():runpy.run_path(str(bonnet))['build_bonnet'](mesh,line,plain,red,black)
    # Open folded-ribbon loops, replacing the earlier filled butterfly shape.
    hair_bow=runpy.run_path(str(OUT/'hair_bow.py'))['build_hair_bow']
    for x,py,angle in [(491,429,-.30),(881,420,.28)]:
        center=Vector(pxy(x,py,-.19))
        hair_bow(mesh,line,uvball,center,1.10,red,black,angle=angle)
    # Thin geometric contours, independent of the illustration alpha.
    H['add_ink_contours'](scene)
    for name,loc,power,size,col in [
      ('key',(-3,-4,4),220,4,(1,.94,.91)),('fill',(3,-3,2),130,4,(.91,.94,1)),('rim',(1,3,3),170,3,(1,.91,.89))]:
        d=bpy.data.lights.new('Head studio | '+name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=col
        o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=loc
        o.rotation_euler=(Vector((0,0,1.4))-o.location).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Head study | camera');cd.type='ORTHO';cd.ortho_scale=2.24
    camera=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(camera);scene.camera=camera
    target=Vector((.01,.06,1.36))
    for name,offset in [('front',(0,-7,0)),('quarter',(4.8,-5,.05)),('side',(7,0,0))]:
        camera.location=target+Vector(offset);camera.rotation_euler=(-Vector(offset)).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    # Clay view proves the underlying geometry from the weakest former angle.
    saved=[];ink=[];clay=plain('Review | clay',(.48,.43,.41),.85)
    for obj in scene.objects:
        if obj.name.startswith('Ink |'):obj.hide_render=True;ink.append(obj)
        elif obj.type in {'MESH','CURVE'}:
            saved.append((obj.data,list(obj.data.materials)))
            for k in range(len(obj.data.materials)):obj.data.materials[k]=clay
    camera.location=target+Vector((4.8,-5,.05));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/'clay-quarter.png');bpy.ops.render.render(write_still=True)
    for data,materials in saved:
        for k,mat in enumerate(materials):data.materials[k]=mat
    for obj in ink:obj.hide_render=False
    camera.location=target+Vector((0,-7,0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    # Write only this scene and recursively used data to an independent file.
    bpy.data.libraries.write(str(OUT/'kurumi-head-study.blend'),{scene},fake_user=True,compress=True)
    meshes=[o for o in scene.objects if o.type=='MESH' and not o.name.startswith('Ink |')]
    bm=bmesh.new();bm.from_mesh(head.data);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free()
    report={'stage':'unapproved head-only study','source_image':REFERENCE.relative_to(BASE).as_posix(),'source_dimensions':list(ref.size),
       'real_meshes':len(meshes),'source_vertices':sum(len(o.data.vertices) for o in meshes),
       'head_nonmanifold_edges':nonmanifold,'packed_reference':bool(ref.packed_file),
       'animation_actions':0,'deployment':False,'method':'closed meshes, calibrated isolated facial UV, dedicated hair albedo along strand UVs'}
    (OUT/'model-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    (OUT/'done.txt').write_text('Head study: front, quarter, side and clay rendered. No deployment.\n')

if __name__=='__main__':render()
