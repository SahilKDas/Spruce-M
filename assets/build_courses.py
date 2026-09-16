"""Assemble six editable art layouts from the Hydro Drift library."""
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Library.blend'))
if 'sand' not in bpy.data.materials:
    m=bpy.data.materials.new('sand'); m.diffuse_color=(.78,.64,.39,1); m.use_nodes=True; m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.78,.64,.39,1)
scene=bpy.context.scene
for lc in scene.view_layers[0].layer_collection.children: lc.exclude=False
for c in bpy.data.collections: c.hide_render=False; c.hide_viewport=False
sources={c.name:list(c.objects) for c in bpy.data.collections}
for c in list(scene.collection.children): scene.collection.children.unlink(c)
scene.render.engine='CYCLES'; scene.cycles.samples=12; scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1000
random.seed(8)
def instance(name,loc,scale=1,rotation=0):
    # Linked mesh data conserves source-file storage. Explicit objects are portable to glTF.
    root=bpy.data.objects.new(name+'_placement',None); course.objects.link(root); root.location=loc; root.rotation_euler.z=rotation; root.scale=(scale,)*3
    for src in sources[name]:
        if src.type not in ['MESH','FONT']:continue
        o=src.copy();o.data=src.data;course.objects.link(o);o.parent=root
    return root
def simple(name,loc,scale,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale
    for c in list(o.users_collection):c.objects.unlink(o)
    course.objects.link(o);o.data.materials.append(bpy.data.materials[material])
    for p in o.data.polygons:p.use_smooth=True
    return o
themes=[('Sunbeam_Lagoon','Palm_tree','Beach_umbrella','sand'),('Neon_Harbor','Harbor_building','Shipping_container','rock'),('Mangrove_Rush','Mangrove_tree','Ruins_arch','sand'),('Glacier_Run','Iceberg','Ice_cluster','ice'),('Stormbreak_Bay','Coastal_rocks','Lighthouse','rock'),('Ember_Atoll','Volcano','Geyser_vent','rock')]
layouts=[]
for idx,(name,feature,accent,ground) in enumerate(themes):
    course=bpy.data.collections.new(name);scene.collection.children.link(course)
    # Race line forms a broad, slightly asymmetric loop around an island.
    points=[]
    for i in range(64):
        a=i*math.tau/64;points.append((math.cos(a)*(34+3*math.sin(a*3)),math.sin(a)*46,.1))
    curve=bpy.data.curves.new(name+'_race_line','CURVE');curve.dimensions='3D';s=curve.splines.new('POLY');s.points.add(63)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=True;o=bpy.data.objects.new('AI_reference_race_line',curve);course.objects.link(o);o.hide_render=True
    simple('Central_island',(0,0,-1.4),(20,31,3.2),ground)
    bpy.ops.mesh.primitive_plane_add(size=180,location=(0,0,0));water=bpy.context.object;water.name='Water_preview_surface'
    for c in list(water.users_collection):c.objects.unlink(water)
    course.objects.link(water)
    water.data.materials.append(bpy.data.materials['blue' if idx in [1,3,4] else 'teal'])
    # Island details and distant silhouettes.
    for i in range(12):
        a=i*math.tau/12
        instance(feature,(math.cos(a)*14,math.sin(a)*23,1.2),2.0 if idx!=5 else 1.3,a)
    for i in range(5):instance(accent,(-10+i*5,(-1 if i%2 else 1)*10,1.5),1.6,i*.8)
    for i in range(0,64,2):
        x,y,z=points[i];a=i*math.tau/64
        for offset in [-5.5,5.5]:instance('Course_buoy',(x+math.cos(a)*offset,y+math.sin(a)*offset,0),1.5)
    instance('Start_finish_arch',(34,0,0),1.6,math.pi/2)
    for i in [12,34,50]:
        x,y,z=points[i];a=i*math.tau/64
        instance('Jump_ramp',(x,y,0),1.8,a+math.pi)
        instance('Pickup_battery',(x,y,2.3),2)
        instance('Direction_sign',(x+math.cos(a)*7,y+math.sin(a)*7,.1),1.6,a+math.pi)
    instance('Dock_3m',(26,-8,.0),2,math.pi/2)
    instance('Harbor_boat',(45,25,.1),2,.5)
    for j,craft in enumerate(['01_Needle_Agile','02_Surge_Balanced','03_Leviathan_Power']):instance(craft,(30+j*3,-7,.0),1,math.pi)
    # Named gates are design references for later engine integration.
    for i in range(0,64,8):
        e=bpy.data.objects.new('Checkpoint_%02d'%(i//8),None);course.objects.link(e);e.location=points[i];e['gate_width_m']=11;e['order']=i//8
    layouts.append({'name':name,'race_line':points,'checkpoint_count':8,'status':'art layout; not a playable or validated race track'})
    bpy.ops.object.select_all(action='DESELECT')
    for o in course.objects:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports'/f'Track_{name}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
    course.hide_render=True;course.hide_viewport=True

presentation=bpy.data.collections.new('Course_Presentation');scene.collection.children.link(presentation)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.lights.new('Sun','SUN');d.energy=2.5;d.angle=.15;sun=bpy.data.objects.new('Sun',d);presentation.objects.link(sun);sun.rotation_euler=(.5,-.4,-.5)
d=bpy.data.cameras.new('CourseCamera');cam=bpy.data.objects.new('CourseCamera',d);presentation.objects.link(cam);scene.camera=cam;cam.location=(95,-120,145);aim(cam,(0,0,0));cam.data.type='ORTHO';cam.data.ortho_scale=148
for idx,(name,*_) in enumerate(themes):
    c=bpy.data.collections[name];c.hide_render=False;c.hide_viewport=False
    scene.render.filepath=str(ROOT/'previews'/f'{idx+4:02d}_{name}.png');bpy.ops.render.render(write_still=True)
    c.hide_render=True;c.hide_viewport=True
bpy.data.collections['Sunbeam_Lagoon'].hide_render=False;bpy.data.collections['Sunbeam_Lagoon'].hide_viewport=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source'/'Hydro_Drift_Courses.blend'),compress=True)
(ROOT/'course_layouts.json').write_text(json.dumps(layouts,indent=2))
print('HYDRO_COURSES_COMPLETE',flush=True)

