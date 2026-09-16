"""Dependency-free GLB structural, geometry and storage audit."""
import json,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
report=[]
for p in sorted((ROOT/'exports').glob('*.glb')):
    data=p.read_bytes(); magic,version,length=struct.unpack_from('<4sII',data)
    assert magic==b'glTF' and version==2 and length==len(data),p.name
    jl,jt=struct.unpack_from('<II',data,12);assert jt==0x4e4f534a
    doc=json.loads(data[20:20+jl]); triangles=0
    for m in doc.get('meshes',[]):
        for prim in m['primitives']:
            assert 'POSITION' in prim['attributes'],p.name
            pos=doc['accessors'][prim['attributes']['POSITION']]
            assert all(math.isfinite(v) for v in pos.get('min',[])+pos.get('max',[])),p.name
            if 'indices' in prim:triangles+=doc['accessors'][prim['indices']]['count']//3
    assert triangles>0,p.name
    for b in doc.get('buffers',[]):assert 'uri' not in b,p.name
    report.append({'file':p.name,'bytes':len(data),'mesh_triangles':triangles,'animations':len(doc.get('animations',[])),'nodes':len(doc.get('nodes',[]))})
total=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
assert total<10_000_000_000,'Storage budget exceeded'
byname={x['file']:x for x in report}
for name,item in byname.items():
    if '_LOD' in name or name.startswith('Track_'):continue
    assert byname[name.replace('.glb','_LOD1.glb')]['mesh_triangles']<=item['mesh_triangles'],name
    assert byname[name.replace('.glb','_LOD2.glb')]['mesh_triangles']<=byname[name.replace('.glb','_LOD1.glb')]['mesh_triangles'],name
result={'file_count':len(report),'storage_bytes':total,'budget_bytes':10_000_000_000,'files':report}
(ROOT/'validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='files'}))
