import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent
report=[]
for name in ['Kai','Zuri','Riptide','Pip','Marina','Bolt','Mochi','Ink']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(R/'exports'/f'{name}.glb'))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
    assert meshes,(name,'No imported deforming mesh')
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rest={}
    for o in meshes:
        ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();rest[o.name]=[v.co.copy() for v in me.vertices];ev.to_mesh_clear()
    bpy.context.scene.frame_set(48);bpy.context.view_layer.update();motion=0
    for o in meshes:
        ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();motion=max(motion,max((v.co-rest[o.name][i]).length for i,v in enumerate(me.vertices)));ev.to_mesh_clear()
    assert motion>.06,(name,'Animation failed after import',motion)
    report.append({'name':name,'imported_skinned_meshes':len(meshes),'max_imported_deformation_m':motion})
(R/'character_import_validation.json').write_text(json.dumps(report,indent=2));print('CHARACTER_IMPORTS_OK',json.dumps(report))
