"""Regression checks for rigid digits and plates in the editable knight sources."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Knights.blend'))
report=[]
for name in ['Kai','Zuri','Riptide','Pip','Marina','Bolt','Mochi','Ink']:
    col=bpy.data.collections[name];rig=next(o for o in col.objects if o.type=='ARMATURE')
    assert len(rig.data.bones)==20 and not any('finger' in b.name.lower() or 'thumb' in b.name.lower() for b in rig.data.bones)
    checked=0;bad=[]
    for obj in col.objects:
        if obj.type!='MESH':continue
        for vertex in obj.data.vertices:
            p=obj.matrix_local@vertex.co
            target=None
            if obj.name.startswith('Kai_AnatomicalBody') and abs(p.x)>.25 and .60<p.z<.91:
                target='hand.'+('L' if p.x<0 else 'R')
            if obj.get('rigid_bone'):target=obj['rigid_bone']
            if obj.get('rigid_pair'):target=obj['rigid_pair']+'.'+('L' if p.x<0 else 'R')
            if target:
                checked+=1
                influences={obj.vertex_groups[g.group].name:g.weight for g in vertex.groups if g.weight>.0001}
                if influences!={target:1.0}:bad.append({'object':obj.name,'vertex':vertex.index,'position':list(p),'influences':influences,'required':target})
    row={'name':name,'bones':20,'finger_bones':0,'rigid_vertices_checked':checked,'invalid_rigid_weights':len(bad)}
    print(row,flush=True)
    if bad:print(bad[:12],flush=True)
    assert not bad,name
    report.append(row)
(ROOT/'knight_source_validation.json').write_text(json.dumps(report,indent=2))
print('KNIGHT_SOURCE_RIG_OK',flush=True)
