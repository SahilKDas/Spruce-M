"""Check the editable body shells rather than merely counting joined objects."""
import bpy, bmesh, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from surface_modeling import components
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Characters_v3.blend'))
report=[]
for name in ['Kai','Zuri','Riptide','Pip','Marina','Bolt','Mochi','Ink']:
    body=next(o for o in bpy.data.collections[name].objects if o.name.startswith(name+'_ConnectedBody'))
    mesh=bmesh.new();mesh.from_mesh(body.data)
    row={'name':name,'body_components':len(components(body)),
         'boundary_edges':sum(e.is_boundary for e in mesh.edges),
         'nonmanifold_edges':sum(not e.is_manifold for e in mesh.edges),
         'loose_vertices':sum(not v.link_faces for v in mesh.verts),
         'control_vertices':len(mesh.verts),'control_faces':len(mesh.faces)}
    mesh.free()
    print(row,flush=True)
    assert row['body_components']==1 and row['boundary_edges']==0 and row['nonmanifold_edges']==0 and row['loose_vertices']==0,row
    report.append(row)
(ROOT/'topology_validation_v3.json').write_text(json.dumps(report,indent=2))
print('V3_TOPOLOGY_OK',flush=True)
