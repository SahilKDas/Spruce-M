"""Replace legacy character collections in the main library with the V2 sources."""
import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent
names=['Kai','Zuri','Riptide','Pip','Marina','Bolt','Mochi','Ink']
bpy.ops.wm.open_mainfile(filepath=str(R/'source/Hydro_Drift_Library.blend'))
scene=bpy.context.scene
for name in names:
    old=bpy.data.collections.get(name)
    if old:
        for obj in list(old.objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.collections.remove(old)
with bpy.data.libraries.load(str(R/'source/Hydro_Drift_Characters.blend'),link=False) as (source,target):target.collections=names
for col in target.collections:
    scene.collection.children.link(col);lc=scene.view_layers[0].layer_collection.children.get(col.name)
    if lc:lc.exclude=True
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/Hydro_Drift_Library.blend'),compress=True)
manifest=json.loads((R/'manifest.json').read_text());updated={x['name']:x for x in json.loads((R/'characters_v2.json').read_text())}
manifest['assets']=[updated.get(x['name'],x) for x in manifest['assets']]
(R/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('V2_INTEGRATED')
