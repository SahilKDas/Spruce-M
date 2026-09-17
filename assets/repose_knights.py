"""Refresh runtime poses from validated neutral LODs, without costly decimation."""
import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from knight_pose import pose,static_grip
for name in ['Kai','Zuri','Riptide','Pip','Marina','Bolt','Mochi','Ink']:
    for index,suffix in [(1,'near'),(2,'far')]:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(ROOT/'exports'/f'{name}_LOD{index}.glb'))
        rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
        # glTF import roots carry the coordinate-system conversion. Restore
        # Blender coordinates before reusing the source-space pose solver.
        rig.rotation_euler=(0,0,0)
        scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=2;scene.frame_set(1)
        for obj in scene.objects:
            if obj.type=='MESH':static_grip(obj)
        pose(rig)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.export_scene.gltf(filepath=str(ROOT.parent/'game/art'/f'{name}_{suffix}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_skins=True,export_def_bones=True,export_animations=True,export_animation_mode='ACTIVE_ACTIONS',export_nla_strips_merged_animation_name='Riding',export_force_sampling=True,export_frame_range=True)
    print('REPOSED',name,flush=True)
print('KNIGHT_POSES_READY',flush=True)
