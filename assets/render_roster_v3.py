"""Render the eight editable revision 3 riders together for silhouette review."""
import bpy, math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Characters_v3.blend'))
scene = bpy.context.scene
studio = bpy.data.collections['V3_Studio']
names = ['Kai', 'Zuri', 'Riptide', 'Pip', 'Marina', 'Bolt', 'Mochi', 'Ink']
for i, name in enumerate(names):
    col = bpy.data.collections[name]
    col.hide_render = False
    scene.view_layers[0].layer_collection.children[name].exclude = True
    instance = bpy.data.objects.new(name+'_Review', None)
    instance.instance_type = 'COLLECTION'
    instance.instance_collection = col
    studio.objects.link(instance)
    instance.location = ((i-3.5)*1.08, 0, 0)
    text = bpy.data.curves.new(name+'_Label', 'FONT')
    text.body = name.upper()
    text.align_x = 'CENTER'
    text.size = .115
    obj = bpy.data.objects.new(name+'_Label', text)
    studio.objects.link(obj)
    obj.location = (instance.location.x, -.32, -.02)
    obj.rotation_euler = (math.pi/2, 0, 0)
    text.materials.append(bpy.data.materials['white'])
camera = scene.camera
camera.location = (0, -13, 3.25)
camera.rotation_euler = (Vector((0, 0, .95))-camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.ortho_scale = 9.1
for obj in studio.objects:
    if obj.type == 'LIGHT':
        obj.data.energy *= 3.5
        obj.data.size *= 2.0
scene.render.resolution_x = 2400
scene.render.resolution_y = 850
scene.cycles.samples = 16
scene.render.filepath = str(ROOT/'previews/17_v3_roster.png')
bpy.ops.render.render(write_still=True)
print('V3_ROSTER_REVIEW_READY', flush=True)
