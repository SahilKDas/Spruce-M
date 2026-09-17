"""Export high-detail source assets and skinned game meshes from revision 3 Blender files."""
import bpy,sys,json,math,shutil
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from surface_modeling import apply_modifiers,components,triangles
OUT=ROOT.parent/'game/art';OUT.mkdir(parents=True,exist_ok=True)
REPORT=[]
if '--riders-only' in sys.argv:
    REPORT=[a for a in json.loads((ROOT/'asset_validation_v3.json').read_text()) if 'bones' not in a]
NAMES=['Kai','Zuri','Riptide','Pip','Marina','Bolt','Mochi','Ink']
def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
def export(path,objects,animated=False):
    select(objects)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_skins=True,export_def_bones=True,export_animations=animated,export_animation_mode='ACTIVE_ACTIONS',export_nla_strips_merged_animation_name='Riding',export_force_sampling=True,export_frame_range=True,export_extras=True)
def reduce_export(mesh,rig,path,target,animated=False):
    mesh.data.calc_loop_triangles();before=len(mesh.data.loop_triangles)
    modifier=mesh.modifiers.new('Geometry budget','DECIMATE');modifier.ratio=min(1,target/before)
    export(path,[mesh,rig] if rig else [mesh],animated)
    mesh.modifiers.remove(modifier)
def merged_copy(collection):
    temp=bpy.data.collections.new('_Export');bpy.context.scene.collection.children.link(temp)
    meshes=[];original_rig=next((o for o in collection.objects if o.type=='ARMATURE'),None);rig=None
    if original_rig:
        rig=original_rig.copy();rig.data=original_rig.data.copy();temp.objects.link(rig);rig.animation_data_clear()
        for pb in rig.pose.bones:
            for con in pb.constraints:
                if con.target==original_rig:con.target=rig
                if con.type=='IK' and con.pole_target==original_rig:con.pole_target=rig
    for original in list(collection.objects):
        if original.type!='MESH':continue
        obj=original.copy();obj.data=original.data.copy();temp.objects.link(obj)
        if rig:obj.parent=rig
        for mod in obj.modifiers:
            mod.show_viewport=True
            if mod.type=='ARMATURE':mod.object=rig
        apply_modifiers(obj);meshes.append(obj)
    select(meshes);bpy.ops.object.join();mesh=bpy.context.object;mesh.name=collection.name+'_GameMesh'
    return mesh,rig,temp
def pose_rider(rig):
    rig.location=(0,.20,.79-rig.data.bones['pelvis'].head_local.z)
    for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0)
    rig.pose.bones['spine'].rotation_euler.x=.22;rig.pose.bones['chest'].rotation_euler.x=.23
    bpy.context.view_layer.update()
    for side in [-1,1]:
        sn='L' if side<0 else 'R'
        for bn,target in [('CTRL_hand',(side*.345,-.400,1.15)),('CTRL_foot',(side*.323,.28,.53)),('CTRL_elbow',(side*.60,-.015,1.23)),('CTRL_knee',(side*.33,-.48,.57))]:
            pb=rig.pose.bones[bn+'.'+sn];matrix=pb.matrix.copy();matrix.translation=rig.matrix_world.inverted()@Vector(target);pb.matrix=matrix
        for bn in ['forearm','shin']:
            for con in rig.pose.bones[bn+'.'+sn].constraints:
                if con.type=='IK':con.influence=1
    bpy.context.view_layer.update();matrices={pb.name:pb.matrix.copy() for pb in rig.pose.bones}
    for pb in rig.pose.bones:
        for con in list(pb.constraints):pb.constraints.remove(con)
    for pb in rig.pose.bones:pb.matrix=matrices[pb.name]
    bpy.context.view_layer.update()
    # Solve both legs in the same geometric plane. Mirrored legacy IK pole angles
    # otherwise bend one knee above the console and the other below the saddle.
    for side in [-1,1]:
        sn='L' if side<0 else 'R'
        thigh=rig.pose.bones['thigh.'+sn];shin=rig.pose.bones['shin.'+sn]
        hip=thigh.matrix.translation.copy()
        ankle=rig.matrix_world.inverted()@Vector((side*.323,.28,.53))
        axis=ankle-hip;distance=axis.length;axis.normalize()
        first=thigh.bone.length;second=shin.bone.length
        along=(first*first-second*second+distance*distance)/(2*distance)
        hint=Vector((side*.16,-1,.15));bend=(hint-axis*hint.dot(axis)).normalized()
        knee=hip+axis*along+bend*math.sqrt(max(0,first*first-along*along))
        for bone,head,tail in [(thigh,hip,knee),(shin,knee,ankle)]:
            rest=bone.bone.matrix_local.to_3x3()
            direction=(tail-head).normalized()
            rotation=(rest@Vector((0,1,0))).rotation_difference(direction).to_matrix()@rest
            bone.matrix=Matrix.Translation(head)@rotation.to_4x4()
            bpy.context.view_layer.update()
    # Fixed hands wrap over the grips; boots stay planted instead of following shin pitch.
    for sn in ['L','R']:
        for name in ['hand.','foot.']:
            pb=rig.pose.bones[name+sn];pb.matrix=Matrix.Translation(pb.matrix.translation)@pb.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
    bpy.context.view_layer.update()
    for frame in [1,2]:
        for pb in rig.pose.bones:
            pb.keyframe_insert('location',frame=frame);pb.keyframe_insert('rotation_euler',frame=frame);pb.keyframe_insert('scale',frame=frame)
    rig.animation_data.action.name='Riding'
def clean_temp(temp):
    for obj in list(temp.objects):bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.collections.remove(temp)

if '--props-only' not in sys.argv:bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Characters_v3.blend'))
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=2;scene.frame_set(1)
for name in ([] if '--props-only' in sys.argv else NAMES):
    for lc in scene.view_layers[0].layer_collection.children:lc.exclude=lc.name!=name
    col=bpy.data.collections[name];body=next(o for o in col.objects if o.name.startswith(name+'_ConnectedBody'))
    assert len(components(body))==1,name+' body shell is disconnected'
    mesh,rig,temp=merged_copy(col)
    names=[b.name for b in rig.data.bones];assert not any('finger' in n.lower() or 'thumb' in n.lower() for n in names)
    unweighted=sum(1 for v in mesh.data.vertices if not v.groups)
    bad=sum(1 for v in mesh.data.vertices if abs(sum(g.weight for g in v.groups)-1)>.002)
    assert unweighted==0 and bad==0,(name,unweighted,bad)
    source=triangles(mesh);export(ROOT/'exports'/f'{name}.glb',[mesh,rig])
    # Reduce each mesh once, then reuse the same geometry for neutral and riding exports.
    # Re-running decimation inside four GLB exports wastes minutes without changing the result.
    reduced=[]
    for index,target in enumerate([160000,45000],1):
        lod=mesh.copy();lod.data=mesh.data.copy();temp.objects.link(lod)
        lod.data.calc_loop_triangles()
        modifier=lod.modifiers.new('Geometry budget','DECIMATE');modifier.ratio=min(1,target/len(lod.data.loop_triangles))
        select([lod]);bpy.ops.object.modifier_apply(modifier=modifier.name)
        export(ROOT/'exports'/f'{name}_LOD{index}.glb',[lod,rig])
        reduced.append(lod)
    pose_rider(rig)
    for suffix,lod in zip(['near','far'],reduced):export(OUT/f'{name}_{suffix}.glb',[lod,rig],True)
    REPORT.append({'name':name,'source_triangles':source,'body_components':1,'bones':len(names),'finger_bones':0,'unweighted_vertices':unweighted,'invalid_weight_sums':bad,'near_target':160000,'far_target':45000})
    print('EXPORTED_RIDER_V3',name,source,flush=True);clean_temp(temp)

for file,names,targets in [
    ('Hydro_Drift_Watercraft_v3.blend',['01_Needle_Agile','02_Surge_Balanced','03_Leviathan_Power'],{}),
    ('Hydro_Drift_Environment_v3.blend',['Palm_tree','Coastal_rocks','Course_buoy','Jump_ramp','Dock_3m','Beach_umbrella','Sunbeam_Island'],{'Palm_tree':30000,'Coastal_rocks':35000,'Course_buoy':4000,'Jump_ramp':18000,'Dock_3m':22000,'Beach_umbrella':18000,'Sunbeam_Island':100000})]:
    if '--riders-only' in sys.argv:continue
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source'/file))
    scene=bpy.context.scene
    for name in names:
        for lc in scene.view_layers[0].layer_collection.children:lc.exclude=lc.name!=name
        mesh,rig,temp=merged_copy(bpy.data.collections[name]);source=triangles(mesh)
        export(ROOT/'exports'/f'{name}.glb',[mesh])
        target=targets.get(name,120000)
        reduce_export(mesh,None,ROOT/'exports'/f'{name}_LOD1.glb',target)
        reduce_export(mesh,None,ROOT/'exports'/f'{name}_LOD2.glb',max(2000,target//3))
        shutil.copy2(ROOT/'exports'/f'{name}_LOD1.glb',OUT/f'{name}.glb')
        if name.startswith(('01_','02_','03_')):shutil.copy2(ROOT/'exports'/f'{name}_LOD2.glb',OUT/f'{name}_far.glb')
        if name=='Course_buoy':shutil.copy2(ROOT/'exports'/f'{name}_LOD2.glb',OUT/f'{name}.glb')
        REPORT.append({'name':name,'source_triangles':source,'runtime_target':target})
        print('EXPORTED_PROP_V3',name,source,flush=True);clean_temp(temp)
(ROOT/'asset_validation_v3.json').write_text(json.dumps(REPORT,indent=2))
(OUT/'runtime_manifest.json').write_text(json.dumps({'revision':3,'assets':REPORT},indent=2))
print('V3_EXPORTS_READY',flush=True)
