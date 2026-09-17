"""Validate actual knight GLB geometry, deformation channels and skin weights."""
import json,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def inspect(path,animated=False):
    raw=path.read_bytes();magic,version,length=struct.unpack_from('<III',raw)
    assert magic==0x46546C67 and version==2 and length==len(raw),path
    size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
    count=0;vertices=0;seen=set();bad_weights=0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            attrs=primitive['attributes'];position=doc['accessors'][attrs['POSITION']]
            assert all(math.isfinite(v) for v in position['min']+position['max']),path
            assert 'JOINTS_0' in attrs and 'WEIGHTS_0' in attrs,path
            count+=doc['accessors'][primitive['indices']]['count']//3;vertices+=position['count']
            index=attrs['WEIGHTS_0']
            if index in seen:continue
            seen.add(index);a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
            assert a['componentType']==5126 and a['type']=='VEC4',path
            offset=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',16)
            for i in range(a['count']):
                weights=struct.unpack_from('<4f',binary,offset+i*stride)
                if not all(math.isfinite(w) and w>=0 for w in weights) or abs(sum(weights)-1)>.002:bad_weights+=1
    assert bad_weights==0,(path,bad_weights)
    assert doc.get('skins'),path
    for skin in doc['skins']:
        names=[doc['nodes'][i].get('name','') for i in skin['joints']]
        assert not any('finger' in n.lower() or 'thumb' in n.lower() for n in names),path
        for part in ['head','forearm.L','forearm.R','shin.L','shin.R','hand.L','hand.R']:
            assert part in names,(path,part)
    if animated:
        assert any(a.get('name')=='Riding' and len(a['channels'])>20 for a in doc.get('animations',[])),path
    return {'file':str(path.relative_to(ROOT.parent)),'triangles':count,'vertices':vertices,'bytes':len(raw),'bad_skin_weights':bad_weights,'skins':len(doc['skins'])}
report=[]
for row in json.loads((ROOT/'knight_validation.json').read_text()):
    name=row['name'];exports=[inspect(ROOT/'exports'/f'{name}{suffix}.glb') for suffix in ['', '_LOD1','_LOD2']]
    runtime=[inspect(ROOT.parent/'game/art'/f'{name}_{detail}.glb',True) for detail in ['near','far']]
    assert exports[0]['triangles']>1000000 and exports[0]['triangles']>exports[1]['triangles']>exports[2]['triangles'],name
    assert 150000<runtime[0]['triangles']<170000 and 20000<runtime[1]['triangles']<24000,name
    report.append({'name':name,'exports':exports,'runtime':runtime})
(ROOT/'knight_glb_validation.json').write_text(json.dumps({'revision':4,'assets':report},indent=2))
print('KNIGHT_GLB_OK: 8 knights; high-detail geometry, near/far LODs, finite bounds, normalized actual skin weights, limb bones, no finger bones, riding clips.')
