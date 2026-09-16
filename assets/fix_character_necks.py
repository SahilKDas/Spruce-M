import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'source/Hydro_Drift_Characters.blend'))
scene=bpy.context.scene;scene.frame_set(1)
heights={'Riptide':1.08,'Pip':.86,'Marina':1.02,'Bolt':1.04,'Mochi':.96,'Ink':1.01}
for name,height in heights.items():
    for lc in scene.view_layers[0].layer_collection.children:lc.exclude=lc.name!=name
    col=bpy.data.collections[name];rig=next(o for o in col.objects if o.type=='ARMATURE');body=next(o for o in col.objects if o.type=='MESH');neck=body.vertex_groups['neck'].index
    for v in body.data.vertices:
        if any(g.group==neck and g.weight>.999 for g in v.groups):
            z=v.co.z/height
            if z>1.53:v.co.z+=min(1,(z-1.53)/.095)*.085*height
    saved=[]
    for pb in rig.pose.bones:
        for con in list(pb.constraints):
            if con.type=='IK':
                saved.append((pb.name,con.name,con.subtarget,con.pole_subtarget,con.chain_count,con.influence));pb.constraints.remove(con)
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
    for level,ratio in [(0,1),(1,.55),(2,.25)]:
        dec=None
        if level:dec=body.modifiers.new('Runtime LOD','DECIMATE');dec.ratio=ratio
        suffix='' if level==0 else '_LOD'+str(level)
        bpy.ops.export_scene.gltf(filepath=str(R/'exports'/f'{name}{suffix}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_skins=True,export_def_bones=True,export_animation_mode='ACTIVE_ACTIONS',export_force_sampling=False,export_animations=(level==0),export_extras=True)
        if dec:body.modifiers.remove(dec)
    for bone,n,target,pole,count,influence in saved:
        con=rig.pose.bones[bone].constraints.new('IK');con.name=n;con.target=rig;con.subtarget=target;con.pole_target=rig;con.pole_subtarget=pole;con.chain_count=count;con.influence=influence
    print('NECK_FIXED',name,flush=True)
for lc in scene.view_layers[0].layer_collection.children:lc.exclude=lc.name!='Presentation_V2'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/Hydro_Drift_Characters.blend'),compress=True)
p=R/'rebuild_characters.py';s=p.read_text();s=s.replace('(1.625,.06,.059)','(1.625 if kind==\'human\' else 1.71,.06,.059)');p.write_text(s)
