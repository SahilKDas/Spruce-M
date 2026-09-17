"""Review the actual game-exported riding pose against the high-detail craft."""
import bpy
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Watercraft_v3.blend'))
bpy.ops.import_scene.gltf(filepath=str(ROOT.parent/'game/art/Kai_near.glb'))
scene=bpy.context.scene
scene.frame_set(1)
camera=scene.camera
camera.location=(3.2,-4.5,2.3)
camera.rotation_euler=(Vector((0,-.05,.90))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale=3.75
scene.cycles.samples=12
scene.render.resolution_x=1300
scene.render.resolution_y=1100
scene.render.filepath=str(ROOT/'previews/26_knight_riding_pose.png')
bpy.ops.render.render(write_still=True)
print('KNIGHT_RIDING_REVIEW_READY',flush=True)
