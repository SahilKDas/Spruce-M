import bpy
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'source/Hydro_Drift_Characters.blend'))
scene=bpy.context.scene;scene.frame_set(1)
for o in list(bpy.data.collections['Presentation_V2'].objects):
    if o.type=='FONT':bpy.data.objects.remove(o,do_unlink=True)
scene.render.resolution_x=2000;scene.render.resolution_y=1000;scene.cycles.samples=10
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL'
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='CUDA';prefs.get_devices()
for dev in prefs.devices:dev.use=dev.type=='CUDA'
scene.cycles.device='GPU'
scene.render.filepath=str(R/'previews/01_characters.png')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/Hydro_Drift_Characters.blend'),compress=True)
bpy.ops.render.render(write_still=True)

