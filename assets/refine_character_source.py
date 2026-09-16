from pathlib import Path
p=Path(__file__).with_name('rebuild_characters.py');s=p.read_text()
helper='''def fuse_human_face(skin):
    global PARTS
    heads=[o for o in PARTS if o.vertex_groups.get('head') and o.data.materials[0]==M[skin]]
    others=[o for o in PARTS if o not in heads]
    bpy.ops.object.select_all(action='DESELECT')
    for o in heads:o.select_set(True)
    bpy.context.view_layer.objects.active=heads[0];bpy.ops.object.join();o=bpy.context.object;o.name='Unified facial skin'
    rem=o.modifiers.new('Fuse facial anatomy','REMESH');rem.mode='VOXEL';rem.voxel_size=.0024;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
    smooth=o.modifiers.new('Relax skin transitions','SMOOTH');smooth.factor=.85;smooth.iterations=5;bpy.ops.object.modifier_apply(modifier=smooth.name)
    o.vertex_groups.clear();bind(o,{'head':1});PARTS=others+[o]
    for obj in PARTS:
        if obj.vertex_groups.get('head'):obj.location.z-=.035

'''
s=s.replace('def make_rider(name,kind,skin,accent,width=1,height=1):',helper+'def make_rider(name,kind,skin,accent,width=1,height=1):')
s=s.replace("if kind=='human':face_human(name,skin)","if kind=='human':\n        face_human(name,skin);fuse_human_face(skin)")
s=s.replace('(1.61,.049,.049),(1.66,.06,.059)','(1.59,.049,.049),(1.625,.06,.059)')
p.write_text(s)
