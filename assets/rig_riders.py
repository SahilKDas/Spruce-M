"""Extend the rigid character rigs with articulated arms/legs and a motion study."""
import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Library.blend'))
scene=bpy.context.scene
for lc in scene.view_layers[0].layer_collection.children:lc.exclude=False
for c in bpy.data.collections:c.hide_viewport=False
names=['Kai','Zuri','Riptide','Pip','Marina','Bolt','Mochi','Ink']
for name in names:
    for lc in scene.view_layers[0].layer_collection.children:lc.exclude=lc.name!=name
    col=bpy.data.collections[name];rig=next(o for o in col.objects if o.type=='ARMATURE')
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    scene.frame_set(1)
    rig.animation_data_clear()
    for pb in rig.pose.bones:pb.rotation_euler=(0,0,0)
    bpy.context.view_layer.update()
    worlds={o:o.matrix_world.copy() for o in col.objects if o!=rig}
    bpy.ops.object.mode_set(mode='EDIT')
    for side in [-1,1]:
        sn='L' if side<0 else 'R';body=rig.data.edit_bones['body']
        upper=rig.data.edit_bones.new('upper_arm_'+sn);upper.head=(side*.31,0,1.33);upper.tail=(side*.46,-.07,1.06);upper.parent=body
        fore=rig.data.edit_bones.new('forearm_'+sn);fore.head=upper.tail;fore.tail=(side*.46,-.31,1.10);fore.parent=upper
        leg=rig.data.edit_bones.new('leg_'+sn);leg.head=(side*.19,0,.86);leg.tail=(side*.19,-.03,.30);leg.parent=body
    bpy.ops.object.mode_set(mode='OBJECT')
    for o,world in worlds.items():
        sn='L' if world.translation.x<0 else 'R'
        if o.name.startswith(('Upper arm','Elbow')):o.parent_bone='upper_arm_'+sn
        if o.name.startswith(('Forearm','Glove')):o.parent_bone='forearm_'+sn
        if o.name.startswith(('Leg','Boot')):o.parent_bone='leg_'+sn
        o.matrix_world=world
    # A labeled motion study for review, not final game animation.
    poses=[(1,0,0,0),(25,0,.025,0),(49,0,0,0),(60,.18,0,.25),(80,.18,-.3,.25),(100,.18,.3,.25),(120,-.12,0,.5),(140,0,0,0),(160,0,0,-1.3),(180,0,0,0)]
    for f,pitch,lean,arms in poses:
        for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0)
        rig.pose.bones['body'].rotation_euler=(pitch,lean,0)
        for sn in ['L','R']:
            rig.pose.bones['upper_arm_'+sn].rotation_euler.x=arms
        for pb in rig.pose.bones:pb.keyframe_insert('rotation_euler',frame=f)
    rig.animation_data.action.name=name+'_Motion_Study'
    scene.frame_start=1;scene.frame_end=180;scene.frame_set(1)
    bpy.ops.object.select_all(action='DESELECT')
    for o in col.objects:o.select_set(True)
    for level,ratio in [(0,1),(1,.5),(2,.22)]:
        mods=[]
        if level:
            for o in col.objects:
                if o.type=='MESH' and len(o.data.polygons)>100:
                    m=o.modifiers.new('Runtime detail reduction','DECIMATE');m.ratio=ratio;mods.append((o,m))
        suffix='' if level==0 else '_LOD'+str(level)
        bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports'/f'{name}{suffix}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_force_sampling=False,export_frame_step=6)
        for o,m in mods:o.modifiers.remove(m)
for marker in list(scene.timeline_markers):scene.timeline_markers.remove(marker)
for label,f in [('Idle',1),('Ride study',60),('Lean left',80),('Lean right',100),('Jump study',120),('Celebrate study',160)]:scene.timeline_markers.new(label,frame=f)
for lc in scene.view_layers[0].layer_collection.children:lc.exclude=lc.name not in ['Presentation','Collection']
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Library.blend'),compress=True)
manifest=json.loads((ROOT/'manifest.json').read_text())
for item in manifest['assets']:
    if item['category']=='character':item['notes']='Nine-bone rigid articulated rig, 180-frame motion study. Not deforming skin or final racing animation.'
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('HYDRO_RIGS_COMPLETE')

