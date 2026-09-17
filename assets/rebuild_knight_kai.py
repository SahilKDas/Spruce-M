"""Hydro Drift knight look-development: realistic anatomy and fitted plate armor.
The CC0 anatomical source is credited in assets/vendor/README.md.
"""
import bpy,bmesh,math,sys,json,random
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from surface_modeling import Surface,sweep,gauss,clamp
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
source=ROOT/'vendor/Blender_CC0_Male_Anatomy.blend'
names=['GEO-body_male_realistic','GEO-body_male_realistic.eye.L','GEO-body_male_realistic.eye.R']
with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.objects=names
col=bpy.data.collections.new('Kai_Realistic');scene.collection.children.link(col)
for obj in dst.objects:col.objects.link(obj)
body=dst.objects[0];offset=body.location.copy()
for obj in dst.objects:obj.location-=offset;obj.hide_render=False;obj.hide_set(False)
body.name='Kai_AnatomicalBody';body['anatomical_source']='Blender Human Base Meshes 1.4.1, realistic male; CC0'
for m in body.modifiers:
    if m.type=='MULTIRES':m.levels=min(2,m.total_levels);m.render_levels=min(3,m.total_levels);print('MULTIRES',m.total_levels,flush=True)

def material(name,color,rough=.5,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m
skin=material('Kai / warm skin',(.43,.24,.145),.49)
p=skin.node_tree.nodes.get('Principled BSDF');p.inputs['Subsurface Weight'].default_value=.085;p.inputs['Subsurface Radius'].default_value=(1,.42,.22)
noise=skin.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=420;noise.inputs['Detail'].default_value=2
bump=skin.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.19;bump.inputs['Distance'].default_value=.00035
skin.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);skin.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
navy=material('Carbon navy neoprene',(.015,.023,.032),.70)
orange=material('Rescue orange woven nylon',(.78,.145,.018),.60)
teal=material('Hydro teal seam tape',(.008,.30,.245),.52)
rubber=material('Matte grip rubber',(.006,.009,.012),.74)
thread=material('Warm silver reflective thread',(.45,.51,.50),.43,.25)
hairmat=material('Dark chestnut hair',(.013,.006,.003),.57)
for mat in [navy,orange]:
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;p=nodes.get('Principled BSDF')
    n=nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=650;n.inputs['Detail'].default_value=2
    b=nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.27;b.inputs['Distance'].default_value=.0006
    links.new(n.outputs['Fac'],b.inputs['Height']);links.new(b.outputs['Normal'],p.inputs['Normal'])
body.data.materials.clear();body.data.materials.append(skin)
for poly in body.data.polygons:poly.use_smooth=True
body.data.materials.append(navy)
for poly in body.data.polygons:
    if poly.center.z<1.44:poly.material_index=1
dep=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(dep);dense=bpy.data.meshes.new_from_object(evaluated,depsgraph=dep)
bvh=BVHTree.FromPolygons([v.co for v in dense.vertices],[list(p.vertices) for p in dense.polygons])

def fitted_y(x,z,offset=.01):
    hit=bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
    return hit[0].y-offset if hit[0] else -.10-offset

def extract(name,predicate,mat,inflate=0):
    bm=bmesh.new();bm.from_mesh(dense)
    remove=[f for f in bm.faces if not predicate(f.calc_center_median())]
    bmesh.ops.delete(bm,geom=remove,context='FACES')
    boundary=[v for v in bm.verts if any(e.is_boundary for e in v.link_edges)]
    for _ in range(8):
        moved=[]
        for v in boundary:
            neighbors=[e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if neighbors:moved.append((v,v.co.lerp(sum((q.co for q in neighbors),Vector())/len(neighbors),.45)))
        for v,point in moved:v.co=point
    bm.normal_update()
    for v in bm.verts:v.co+=v.normal*inflate
    mesh=bpy.data.meshes.new(name);bm.to_mesh(mesh);bm.free()
    obj=bpy.data.objects.new(name,mesh);col.objects.link(obj);mesh.materials.append(mat)
    for poly in mesh.polygons:poly.use_smooth=True;poly.material_index=0
    return obj

# Clothing follows anatomical topology. Relaxed surfaces suppress bare-body details.
suit=extract('Tailored short-sleeve wetsuit',lambda p:.10<p.z<1.435 and (abs(p.x)<.22 or p.z>1.13),navy,.009)
smooth=suit.modifiers.new('Relax neoprene', 'SMOOTH');smooth.factor=.8;smooth.iterations=10
solid=suit.modifiers.new('Neoprene thickness','SOLIDIFY');solid.thickness=.003
for v in suit.data.vertices:
    x,y,z=v.co
    if abs(x)<.11 and .74<z<.91 and y<-.01:
        v.co.y=min(y,-.104+.035*((z-.83)/.10)**2)
suit.data.materials.append(teal)
for poly in suit.data.polygons:
    if abs(poly.center.x)>.165 and poly.center.z>1.28:poly.material_index=1

def cord(name,points,radius,mat):
    surf=Surface(name);sweep(surf,points,[radius]*len(points),segments=8);return surf.obj(col,[mat],1)

from knight_armor import build_armor
build_armor(col,extract,material,cord)

# The original fitted eyes preserve real sockets and corneal curvature.
eye_white=material('Natural sclera',(.56,.59,.53),.24)
iris=material('Blue green iris',(.023,.13,.12),.28)
pupil=material('Deep pupil',(.001,.002,.002),.12)
for obj in [o for o in col.objects if '.eye.' in o.name]:
    obj.data.materials.clear()
    for mat in [eye_white,iris,pupil]:obj.data.materials.append(mat)
    for face in obj.data.polygons:
        c=face.center;radius=math.sqrt(c.x*c.x+c.z*c.z)
        face.material_index=2 if c.y<0 and radius<.0035 else (1 if c.y<0 and radius<.0065 else 0)
        face.use_smooth=True

# A deformation skeleton with real elbows/knees and rigid, unarticulated fingers.
arm=bpy.data.armatures.new('Kai body skeleton');rig=bpy.data.objects.new('Kai_Realistic_Rig',arm);col.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
def bone(name,head,tail,parent=None):
    b=arm.edit_bones.new(name);b.head=head;b.tail=tail
    if parent:b.parent=arm.edit_bones[parent]
bone('root',(0,0,0),(0,0,.15));bone('pelvis',(0,0,.86),(0,0,.99),'root');bone('spine',(0,0,.99),(0,0,1.19),'pelvis');bone('chest',(0,0,1.19),(0,0,1.40),'spine');bone('neck',(0,0,1.40),(0,0,1.50),'chest');bone('head',(0,0,1.50),(0,-.01,1.67),'neck')
for side in [-1,1]:
    sn='L' if side<0 else 'R'
    bone('clavicle.'+sn,(0,0,1.36),(side*.17,0,1.37),'chest')
    bone('upper_arm.'+sn,(side*.17,0,1.37),(side*.292,-.006,1.14),'clavicle.'+sn)
    bone('forearm.'+sn,(side*.292,-.006,1.14),(side*.383,-.018,.936),'upper_arm.'+sn)
    bone('hand.'+sn,(side*.383,-.018,.936),(side*.414,-.022,.83),'forearm.'+sn)
    bone('thigh.'+sn,(side*.095,0,.86),(side*.12,-.023,.48),'pelvis')
    bone('shin.'+sn,(side*.12,-.023,.48),(side*.163,.049,.095),'thigh.'+sn)
    bone('foot.'+sn,(side*.163,.049,.095),(side*.173,-.12,.045),'shin.'+sn)
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True

def weights(point):
    x,y,z=point;sn='L' if x<0 else 'R';xx=abs(x)
    if z>1.48:return {'head':1}
    if xx>.355 and z<.99:return {'hand.'+sn:1}
    if xx>.205 and z>.77:
        if z<.99:return {'hand.'+sn:1}
        if z<1.09:return {'forearm.'+sn:1}
        if z<1.20:
            t=clamp((z-1.09)/.11);return {'forearm.'+sn:1-t,'upper_arm.'+sn:t}
        if z<1.33:return {'upper_arm.'+sn:1}
        return {'clavicle.'+sn:.35,'upper_arm.'+sn:.65}
    if z<.91:
        if z<.12:return {'foot.'+sn:1}
        if z<.43:return {'shin.'+sn:1}
        if z<.54:
            t=(z-.43)/.11;return {'shin.'+sn:1-t,'thigh.'+sn:t}
        if z<.79:return {'thigh.'+sn:1}
        t=clamp((z-.79)/.12);return {'thigh.'+sn:1-t,'pelvis':t}
    if z<1.07:return {'pelvis':.3,'spine':.7}
    if z<1.27:return {'spine':.3,'chest':.7}
    if z<1.41:return {'chest':1}
    return {'neck':1}
for obj in list(col.objects):
    if obj.type!='MESH':continue
    groups={b.name:obj.vertex_groups.new(name=b.name) for b in arm.bones}
    for v in obj.data.vertices:
        p=obj.matrix_world@v.co
        w={obj['rigid_bone']:1} if obj.get('rigid_bone') else {obj['rigid_pair']+'.'+('L' if p.x<0 else 'R'):1} if obj.get('rigid_pair') else {'head':1} if ('hair' in obj.name.lower() or 'fiber' in obj.name.lower() or '.eye.' in obj.name) else weights(p)
        for name,value in w.items():
            if value>0:groups[name].add([v.index],value,'REPLACE')
    obj.parent=rig;mod=obj.modifiers.new('Body deformation','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
rig['fingers']='Static geometry attached to each hand. No finger bones.'

studio=bpy.data.collections.new('Review_Studio');scene.collection.children.link(studio)
floor=Surface('Floor');floor.v=[(-20,-20,-.01),(20,-20,-.01),(20,20,-.01),(-20,20,-.01)];floor.w=[{}]*4;floor.face((0,1,2,3));floor.obj(studio,[material('Warm charcoal studio',(.038,.045,.05),.85)])
def aim(obj,point):obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Softbox',(-2.5,-3,4),420,3),('Fill',(3,-1,2.4),160,2.5),('Rim',(1,2,3),500,2)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size;obj=bpy.data.objects.new(name,data);studio.objects.link(obj);obj.location=loc;aim(obj,(0,0,1.1))
world=bpy.data.worlds.new('Studio world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.20,.22,1);world.node_tree.nodes['Background'].inputs[1].default_value=.3;scene.world=world
data=bpy.data.cameras.new('Realistic review');camera=bpy.data.objects.new('Realistic review',data);studio.objects.link(camera);scene.camera=camera
camera.location=(1.2,-4.5,1.85);aim(camera,(0,0,.90));data.type='ORTHO';data.ortho_scale=2.15
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1400;scene.render.resolution_y=1600;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
scene['art_direction']='Realistic anatomy and smooth sculpted forms; fitted racing apparel. Review prototype.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Knight_Kai.blend'),compress=True)
if '--no-render' in sys.argv:
    print('KNIGHT_KAI_READY',flush=True);sys.exit(0)
scene.render.filepath=str(ROOT/'previews/23_knight_kai_body.png');bpy.ops.render.render(write_still=True)
camera.location=(.32,-2.5,1.67);aim(camera,(0,-.025,1.54));data.ortho_scale=.49
scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.filepath=str(ROOT/'previews/24_knight_kai_helmet.png');bpy.ops.render.render(write_still=True)
print('KNIGHT_KAI_READY',flush=True)
