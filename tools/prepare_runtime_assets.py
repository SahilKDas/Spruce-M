"""Create posed, skinned runtime riders from the committed Blender sources."""
import bpy,json,math,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'game/art';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/source/Hydro_Drift_Characters.blend'))
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=2;scene.frame_set(1)
names=['Kai','Zuri','Riptide','Pip','Marina','Bolt','Mochi','Ink'];report=[]
for name in names:
    for lc in scene.view_layers[0].layer_collection.children:lc.exclude=lc.name!=name
    col=bpy.data.collections[name];rig=next(o for o in col.objects if o.type=='ARMATURE');body=next(o for o in col.objects if o.type=='MESH')
    rig.animation_data_clear()
    for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0)
    rig.location=(0,.20,-.10)
    rig.pose.bones['spine'].rotation_euler.x=.30
    rig.pose.bones['chest'].rotation_euler.x=.28
    bpy.context.view_layer.update()
    for side in [-1,1]:
        sn='L' if side<0 else 'R'
        for bn,target in [('CTRL_hand',(side*.34,-.37,1.10)),('CTRL_foot',(side*.43,.28,.67)),('CTRL_elbow',(side*.65,-.05,1.25)),('CTRL_knee',(side*.39,-.55,.50))]:
            pb=rig.pose.bones[bn+'.'+sn];m=pb.matrix.copy();m.translation=rig.matrix_world.inverted()@Vector(target);pb.matrix=m
        for bn in ['forearm','shin']:
            for con in rig.pose.bones[bn+'.'+sn].constraints:
                if con.type=='IK':con.influence=1
    bpy.context.view_layer.update()
    # Bake IK matrices to FK so runtime rigs need no IK solver.
    pose_matrices={pb.name:pb.matrix.copy() for pb in rig.pose.bones}
    for pb in rig.pose.bones:
        for con in list(pb.constraints):pb.constraints.remove(con)
    for pb in rig.pose.bones:pb.matrix=pose_matrices[pb.name]
    bpy.context.view_layer.update()
    for f in [1,2]:
        for pb in rig.pose.bones:
            pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_euler',frame=f);pb.keyframe_insert('scale',frame=f)
    rig.animation_data.action.name='Riding'
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=rig
    body.data.calc_loop_triangles();source_tris=len(body.data.loop_triangles)
    for suffix,target in [('near',36000),('far',11000)]:
        dec=body.modifiers.new('Race mesh budget','DECIMATE');dec.ratio=min(1,target/source_tris)
        bpy.ops.export_scene.gltf(filepath=str(OUT/f'{name}_{suffix}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_skins=True,export_def_bones=True,export_animation_mode='ACTIVE_ACTIONS',export_force_sampling=True,export_frame_range=True,export_extras=False)
        body.modifiers.remove(dec)
        report.append({'rider':name,'detail':suffix,'source_triangles':source_tris,'target_triangles':target})
    print('RUNTIME_RIDER',name,flush=True)
for name in ['01_Needle_Agile','02_Surge_Balanced','03_Leviathan_Power','Palm_tree','Coastal_rocks','Course_buoy','Jump_ramp','Dock_3m','Beach_umbrella']:
    shutil.copy2(ROOT/'assets/exports'/f'{name}_LOD2.glb',OUT/f'{name}.glb')
(OUT/'runtime_manifest.json').write_text(json.dumps(report,indent=2))
print('RUNTIME_ASSETS_READY',flush=True)
