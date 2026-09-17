"""Audit the actual exported GLBs, including skins, static digits, and LOD counts."""
import json, math, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<III', data)
    assert magic == 0x46546C67 and version == 2 and length == len(data), path
    size, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4E4F534A, path
    return json.loads(data[20:20+size])

def inspect(path, rider=False, animated=False):
    doc = read_glb(path)
    triangles = 0
    for mesh in doc['meshes']:
        for surface in mesh['primitives']:
            assert surface.get('mode', 4) == 4, path
            attributes = surface['attributes']
            pos = doc['accessors'][attributes['POSITION']]
            assert pos['count'] > 0 and all(math.isfinite(v) for v in pos['min']+pos['max']), path
            triangles += doc['accessors'][surface['indices']]['count']//3
            if rider:
                assert 'JOINTS_0' in attributes and 'WEIGHTS_0' in attributes, path
    if rider:
        assert doc.get('skins'), path
        for skin in doc['skins']:
            bone_names = [doc['nodes'][i].get('name', '').lower() for i in skin['joints']]
            assert not any('finger' in n or 'thumb' in n for n in bone_names), path
            for bone in ('pelvis', 'head', 'upper_arm.L', 'forearm.L', 'thigh.L', 'shin.L'):
                assert bone.lower() in bone_names, (path, bone)
        if animated:
            assert any(a.get('name') == 'Riding' for a in doc.get('animations', [])), path
    return {'file': str(path.relative_to(ROOT.parent)), 'triangles': triangles, 'bytes': path.stat().st_size,
            'material_surfaces': sum(len(m['primitives']) for m in doc['meshes']),
            'skins': len(doc.get('skins', [])), 'animations': len(doc.get('animations', []))}

source_report = json.loads((ROOT/'asset_validation_v3.json').read_text())
report = []
for asset in source_report:
    name = asset['name']
    rider = 'bones' in asset
    files = [inspect(ROOT/'exports'/f'{name}{suffix}.glb', rider) for suffix in ('', '_LOD1', '_LOD2')]
    assert files[0]['triangles'] >= files[1]['triangles'] >= files[2]['triangles'], name
    assert abs(files[0]['triangles']-asset['source_triangles']) < 50, name
    if rider:
        runtime = [inspect(ROOT.parent/'game/art'/f'{name}_{lod}.glb', True, True) for lod in ('near', 'far')]
        assert 150000 <= runtime[0]['triangles'] <= 170000, name
        assert 40000 <= runtime[1]['triangles'] <= 50000, name
    else:
        runtime = [inspect(ROOT.parent/'game/art'/f'{name}.glb')]
        assert runtime[0]['triangles'] == files[1]['triangles'], name
    report.append({'name': name, 'exports': files, 'runtime': runtime})
(ROOT/'glb_validation_v3.json').write_text(json.dumps({'revision': 3, 'assets': report}, indent=2))
print(f'V3_GLB_VALIDATION_OK {len(report)} assets; source/LOD ordering, bounds, limb skinning, static fingers, riding actions')
