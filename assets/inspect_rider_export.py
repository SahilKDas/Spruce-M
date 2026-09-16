import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'exports/Kai.glb'))
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
for o in bpy.context.scene.objects:
    if o.type=='MESH': print('PART',o.name,tuple(o.dimensions),tuple(o.matrix_world.translation))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=700;scene.render.resolution_y=700
scene.world=bpy.data.worlds.new('World');scene.world.color=(.3,.3,.3)
d=bpy.data.lights.new('Key','AREA');d.energy=600;d.size=5;o=bpy.data.objects.new('Key',d);scene.collection.objects.link(o);o.location=(2,-4,6)
d=bpy.data.cameras.new('Camera');o=bpy.data.objects.new('Camera',d);scene.collection.objects.link(o);scene.camera=o;o.location=(4,-7,4);o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=4
scene.render.filepath=str(R/'previews/10_import_check.png');bpy.ops.render.render(write_still=True)
