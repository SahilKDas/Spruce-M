"""Render the committed revision 3 Kai source at body and face scale."""
import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Characters_v3.blend'))
scene=bpy.context.scene
scene.cycles.samples=16
scene.render.filepath=str(ROOT/'previews/14_v3_rider_closeup.png')
bpy.ops.render.render(write_still=True)
camera=scene.camera
camera.data.ortho_scale=.48
camera.location=(.55,-2,1.90)
camera.rotation_euler=(Vector((0,-.025,1.79))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(ROOT/'previews/15_v3_face.png')
bpy.ops.render.render(write_still=True)
print('V3_CLOSEUP_REVIEW_READY',flush=True)
