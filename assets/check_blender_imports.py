import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
results=[]
for name in ['Kai.glb','Kai_LOD2.glb','03_Leviathan_Power.glb','Palm_tree.glb','Track_Sunbeam_Lagoon.glb']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'exports'/name))
    bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
    bone_shapes={pb.custom_shape for rig in bpy.context.scene.objects if rig.type=='ARMATURE' for pb in rig.pose.bones if pb.custom_shape}
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH' and o not in bone_shapes]
    assert obs,name
    coords=[o.matrix_world@Vector(v) for o in obs for v in o.bound_box]
    bounds=[max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)]
    assert min(bounds)>0 and max(bounds)<300,(name,bounds)
    results.append({'file':name,'mesh_objects':len(obs),'bounds_m':bounds,'actions':len(bpy.data.actions)})
(ROOT/'import_validation.json').write_text(json.dumps(results,indent=2))
print('BLENDER_IMPORTS_OK',json.dumps(results))


