import bpy,json,struct
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'source/Hydro_Drift_Characters.blend'))
inventory=json.loads((R/'characters_v2.json').read_text());report=[]
for item in inventory:
    name=item['name'];col=bpy.data.collections[name];rig=next(o for o in col.objects if o.type=='ARMATURE');body=next(o for o in col.objects if o.type=='MESH')
    assert not any('finger' in b.name.lower() or 'thumb' in b.name.lower() for b in rig.data.bones),name
    for side in ['L','R']:
        for joint in ['upper_arm','forearm','hand','thigh','shin','foot']:assert joint+'.'+side in rig.data.bones,(name,joint)
    assert any(m.type=='ARMATURE' and m.object==rig for m in body.modifiers),name
    unweighted=[v.index for v in body.data.vertices if abs(sum(g.weight for g in v.groups)-1)>0.005]
    assert not unweighted,(name,'Invalid skin weights',len(unweighted))
    for lc in bpy.context.scene.view_layers[0].layer_collection.children:lc.exclude=lc.name!=name
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    rest_eval=body.evaluated_get(bpy.context.evaluated_depsgraph_get());rest_mesh=rest_eval.to_mesh();rest_positions=[v.co.copy() for v in rest_mesh.vertices];rest_eval.to_mesh_clear()
    bpy.context.scene.frame_set(60);bpy.context.view_layer.update()
    bend_eval=body.evaluated_get(bpy.context.evaluated_depsgraph_get());bend_mesh=bend_eval.to_mesh();max_motion=max((v.co-rest_positions[i]).length for i,v in enumerate(bend_mesh.vertices));bend_eval.to_mesh_clear()
    assert max_motion>.08,(name,'Skin is not deforming',max_motion)
    bpy.context.scene.frame_set(1)
    meshes=[]
    for suffix in ['', '_LOD1','_LOD2']:
        data=(R/'exports'/f'{name}{suffix}.glb').read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size])
        assert len(doc.get('skins',[]))==1,(name,suffix,'Missing skin')
        if not suffix:assert doc.get('animations'),(name,suffix,'Missing pose test')
        tri=0
        for mesh in doc['meshes']:
            for p in mesh['primitives']:
                assert 'JOINTS_0' in p['attributes'] and 'WEIGHTS_0' in p['attributes'],(name,suffix,'Unskinned primitive')
                tri+=doc['accessors'][p['indices']]['count']//3
        meshes.append(tri)
    assert meshes[0]>=meshes[1]>=meshes[2],(name,meshes)
    report.append({'name':name,'skin_weight_errors':0,'finger_bones':0,'bones':len(rig.data.bones),'vertices':len(body.data.vertices),'lod_triangles':meshes,'embedded_skin':True,'max_pose_deformation_m':max_motion})
(R/'character_validation.json').write_text(json.dumps(report,indent=2));print('CHARACTER_VALIDATION_OK',json.dumps(report))

