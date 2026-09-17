import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parent
source=next((root/'vendor/blender-human-base').rglob('*.blend'))
bpy.ops.wm.open_mainfile(filepath=str(source))
for text in bpy.data.texts:print('TEXT',text.name,text.as_string()[:6000],flush=True)
report=[]
for o in bpy.data.objects:
    row={'name':o.name,'type':o.type,'location':list(o.location),'scale':list(o.scale),'dimensions':list(o.dimensions),'modifiers':[(m.name,m.type) for m in o.modifiers]}
    if o.type=='MESH':row.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),groups=[g.name for g in o.vertex_groups])
    if o.asset_data:row.update(author=o.asset_data.author,license=o.asset_data.license,description=o.asset_data.description)
    report.append(row)
(root/'anatomy_inventory.json').write_text(json.dumps(report,indent=2))
print('ANATOMY_INVENTORY_READY',flush=True)
