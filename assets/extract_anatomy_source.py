"""Keep only the CC0 anatomical body and eyes used by Hydro Drift."""
import bpy
from pathlib import Path
root=Path(__file__).resolve().parent
source=next((root/'vendor/blender-human-base').rglob('*.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(source),link=False) as (src,dst):
    dst.objects=['GEO-body_male_realistic','GEO-body_male_realistic.eye.L','GEO-body_male_realistic.eye.R']
bpy.data.libraries.write(str(root/'vendor/Blender_CC0_Male_Anatomy.blend'),set(dst.objects),fake_user=True,compress=True)
print('CC0_ANATOMY_EXTRACTED',flush=True)
