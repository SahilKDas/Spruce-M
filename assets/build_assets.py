"""Hydro Drift original procedural asset library. Run with Blender --background --python."""
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
for d in ['exports','previews','source']:
    (ROOT/d).mkdir(exist_ok=True)
random.seed(21)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
MAT={}
def mat(name, color, metallic=0, rough=.38, emission=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metallic; p.inputs['Roughness'].default_value=rough
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emission
    MAT[name]=m; return m
for n,c in {'navy':(.018,.035,.07),'white':(.87,.94,.93),'teal':(.015,.65,.58),'orange':(1,.22,.035),'yellow':(1,.7,.055),'pink':(.95,.22,.46),'purple':(.33,.12,.61),'blue':(.055,.28,.64),'skin':(.6,.29,.15),'skin2':(.26,.105,.065),'brown':(.29,.12,.055),'tan':(.65,.4,.19),'sand':(.78,.64,.39),'green':(.055,.32,.16),'leaf':(.18,.57,.22),'rock':(.2,.26,.29),'ice':(.35,.8,.9),'lava':(1,.13,.015)}.items(): mat(n,c,rough=.42)
mat('metal',(.38,.48,.53),.75,.25); mat('glass',(.035,.14,.21),.55,.16); mat('glow',(.05,.9,1),.2,.22,2)
current=None
def add(o,name,m):
    o.name=name
    for c in list(o.users_collection): c.objects.unlink(o)
    current.objects.link(o)
    if m: o.data.materials.append(MAT[m])
    if o.type=='MESH':
        for p in o.data.polygons: p.use_smooth=True
    return o
def uv(n,p,s,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=p); o=bpy.context.object; o.scale=s
    return add(o,n,m)
def cube(n,p,s,m,bevel=.08):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p); o=bpy.context.object; o.scale=s
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new('Soft manufactured edges','BEVEL'); b.width=bevel; b.segments=3
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return add(o,n,m)
def rod(n,a,b,r,m,r2=None):
    a,b=Vector(a),Vector(b); delta=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=r,radius2=r if r2 is None else r2,depth=delta.length,location=(a+b)/2)
    o=bpy.context.object; o.rotation_euler=delta.to_track_quat('Z','Y').to_euler(); return add(o,n,m)
def torus(n,p,major,minor,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=10,location=p,major_radius=major,minor_radius=minor,rotation=rot)
    return add(bpy.context.object,n,m)
def mesh(n,verts,faces,m):
    d=bpy.data.meshes.new(n); d.from_pydata(verts,[],faces); d.update(); o=bpy.data.objects.new(n,d); current.objects.link(o); d.materials.append(MAT[m]); return o
def text(n,body,p,size,m,rot=(math.pi/2,0,0)):
    d=bpy.data.curves.new(n,'FONT'); d.body=body; d.align_x='CENTER'; d.size=size; d.extrude=.004
    o=bpy.data.objects.new(n,d); current.objects.link(o); o.location=p; o.rotation_euler=rot; d.materials.append(MAT[m]); return o
catalog=[]
def start(name,category):
    global current
    current=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(current)
    current['category']=category
    return current
def finish(name,category,notes=''):
    obs=list(current.objects)
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    if obs: bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports'/f'{name}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
    tris=0
    for o in obs:
        if o.type=='MESH':
            ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh(); me.calc_loop_triangles(); tris+=len(me.loop_triangles); ev.to_mesh_clear()
    # Each LOD is exported separately so engines can assign their own thresholds.
    mods=[]
    for level,ratio in [(1,.5),(2,.22)]:
        for o in obs:
            if o.type=='MESH' and len(o.data.polygons)>100:
                mod=o.modifiers.new('Runtime detail reduction','DECIMATE'); mod.ratio=ratio; mods.append((o,mod))
        bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports'/f'{name}_LOD{level}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
        for o,mod in mods: o.modifiers.remove(mod)
        mods=[]
    catalog.append(dict(name=name,category=category,triangles_lod0=tris,notes=notes))
    current.hide_render=True; current.hide_viewport=True

def character(name,kind,color):
    start(name,'character')
    # Jointed toy-like anatomy makes an inexpensive rigid-part rig possible.
    uv('Torso',(0,0,1.1),(.32,.22,.4),color)
    uv('Flotation vest',(0,-.015,1.14),(.35,.24,.29),'orange' if kind in ['human','capy'] else 'teal')
    for x in [-.18,.18]:
        cube('Vest reflective strip',(x,-.244,1.2),(.065,.018,.27),'white',.01)
    cube('Vest buckle',(0,-.267,1.03),(.15,.04,.08),'navy',.015)
    head=uv('Head',(0,0,1.71),(.32,.27,.32),color)
    for x in [-.115,.115]:
        uv('Eye white',(x,-.25,1.77),(.09,.04,.105),'white')
        uv('Pupil',(x,-.284,1.77),(.042,.019,.063),'navy')
        uv('Eye glint',(x-.013,-.302,1.798),(.013,.007,.018),'white')
    if kind=='human':
        uv('Hair cap',(0,.035,1.94),(.33,.27,.14),'navy' if name=='Kai' else 'brown')
        for x in [-.31,.31]: uv('Ear',(x,0,1.73),(.06,.06,.095),color)
        uv('Nose',(0,-.287,1.68),(.055,.07,.065),color)
        if name=='Zuri':
            for x in [-.24,.24]: uv('Hair puff',(x,.11,1.98),(.16,.16,.17),'brown')
        else:
            cube('Headband',(0,-.22,1.94),(.55,.09,.07),'teal',.025)
    if kind in ['otter','capy']:
        uv('Muzzle',(0,-.245,1.59),(.23,.1,.13),'tan')
        uv('Nose',(0,-.34,1.65),(.075,.04,.045),'navy')
        for x in [-.27,.27]: uv('Round ear',(x,0,1.94),(.09,.065,.09),color)
        if kind=='otter':
            rod('Tail',(0,.14,.9),(0,.64,.36),.12,color,.045)
            for x in [-.115,.115]: torus('Goggle frame',(x,-.30,1.78),.105,.018,'yellow',(math.pi/2,0,0))
    if kind=='shark':
        uv('Snout',(0,-.20,1.58),(.29,.18,.12),'white')
        mesh('Dorsal fin',[(0,.16,1.4),(0,.62,1.15),(0,.2,.93),(.085,.2,1.1),(-.085,.2,1.1)],[(0,1,3),(1,2,3),(0,4,1),(1,4,2),(0,3,4),(2,4,3)],'blue')
        for x in [-.1,0,.1]: rod('Tooth',(x,-.35,1.54),(x,-.35,1.48),.025,'white',0)
    if kind=='axolotl':
        for side in [-1,1]:
            for i in range(3):
                a=(side*.26,0,1.65+i*.12); b=(side*(.46+(.08 if i==1 else 0)),0,1.64+i*.16)
                rod('External gill',a,b,.034,'pink',.05); uv('Gill tip',b,(.07,.035,.09),'pink')
        torus('Tiara',(0,0,1.98),.21,.025,'yellow')
        for x in [-.12,0,.12]: rod('Crown spike',(x,-.12,1.99),(x,-.12,2.12+(0.05 if x==0 else 0)),.035,'yellow',0)
    if kind=='robot':
        head.hide_render=True; bpy.data.objects.remove(head,do_unlink=True)
        cube('Robot head',(0,0,1.74),(.65,.47,.48),'metal',.12)
        cube('Face screen',(0,-.251,1.75),(.51,.035,.29),'navy',.06)
        for x in [-.12,.12]: cube('LED eye',(x,-.277,1.77),(.055,.025,.11),'glow',.02)
        rod('Antenna',(0,0,1.98),(0,0,2.15),.025,'metal'); uv('Antenna light',(0,0,2.18),(.06,)*3,'orange')
    if kind=='octopus':
        for i in range(4):
            x=(i-1.5)*.15
            rod('Extra tentacle',(x,.12,.98),(x*2,.39,.64),.09,color,.055)
            uv('Tentacle tip',(x*2,.39,.64),(.09,.09,.07),color)
    for side in [-1,1]:
        x=side*.19
        rod('Leg',(x,0,.86),(x,-.03,.44),.115,color,.1)
        uv('Boot',(x,-.095,.30),(.13,.22,.14),'navy')
        a=(side*.31,0,1.33); b=(side*.46,-.07,1.06); c=(side*.46,-.31,1.10)
        rod('Upper arm',a,b,.095,color,.08); uv('Elbow',b,(.08,)*3,color); rod('Forearm',b,c,.08,color,.07); uv('Glove',c,(.095,.09,.09),'navy')
    # Rigid attachment to bones preserves the deliberate articulated style.
    obs=list(current.objects)
    arm=bpy.data.armatures.new(name+'_skeleton'); rig=bpy.data.objects.new(name+'_Rig',arm); current.objects.link(rig)
    bpy.context.view_layer.objects.active=rig; rig.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    root=arm.edit_bones.new('root'); root.head=(0,0,0); root.tail=(0,0,.35)
    body=arm.edit_bones.new('body'); body.head=(0,0,.85); body.tail=(0,0,1.4); body.parent=root
    neck=arm.edit_bones.new('head'); neck.head=(0,0,1.45); neck.tail=(0,0,2); neck.parent=body
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in obs:
        world=o.matrix_world.copy(); o.parent=rig; o.parent_type='BONE'; o.parent_bone='head' if o.location.z>1.45 and o.type!='FONT' else 'body'; o.matrix_world=world
    proportions={'human':(1,1,1),'shark':(1.30,1.15,1.12),'otter':(.82,.88,.87),'axolotl':(.95,.96,1.03),'robot':(1.04,1,1.06),'capy':(1.28,1.1,.92),'octopus':(1.06,1.03,.96)}
    rig.scale=proportions[kind]; rig.location.z=-.16*rig.scale.z
    for frame,angle in [(1,-.025),(25,.025),(49,-.025)]:
        rig.pose.bones['body'].rotation_mode='XYZ'; rig.pose.bones['body'].rotation_euler.y=angle; rig.pose.bones['body'].keyframe_insert('rotation_euler',frame=frame)
    if rig.animation_data and rig.animation_data.action: rig.animation_data.action.name=name+'_Idle'
    bpy.context.scene.frame_set(1)
    finish(name,'character','Articulated style; root/body/head rigid bone rig with idle. Limb animation and skin deformation remain to be authored.')

for args in [('Kai','human','skin'),('Zuri','human','skin2'),('Riptide','shark','blue'),('Pip','otter','brown'),('Marina','axolotl','pink'),('Bolt','robot','metal'),('Mochi','capy','tan'),('Ink','octopus','purple')]: character(*args)

def craft(name,color,width,length):
    start(name,'watercraft')
    # Sculpted ring hull, bow at negative Y.
    rings=[(-length*.52,.045,.18),(-length*.40,width*.60,.26),(-length*.15,width,.30),(length*.30,width*.90,.26),(length*.48,width*.65,.19)]
    verts=[]
    for y,w,h in rings:
        for j in range(12):
            a=2*math.pi*j/12; verts.append((math.cos(a)*w,y,.40+math.sin(a)*h))
    faces=[]
    for i in range(4):
        for j in range(12): faces.append((i*12+j,i*12+(j+1)%12,(i+1)*12+(j+1)%12,(i+1)*12+j))
    faces += [tuple(range(11,-1,-1)),tuple(range(48,60))]
    hull=mesh('Sculpted hull',verts,faces,color); sub=hull.modifiers.new('Hull curvature','SUBSURF'); sub.levels=2
    for p in hull.data.polygons:p.use_smooth=True
    uv('Lower hull',(0,.08,.29),(width*.93,length*.44,.19),'navy')
    uv('Saddle',(0,.27,.76),(.24,length*.23,.15),'navy')
    uv('Front cowl',(0,-length*.20,.70),(width*.58,.39,.27),color)
    uv('Instrument glass',(0,-length*.19,.91),(.18,.16,.05),'glass')
    rod('Steering column',(0,-.35,.75),(0,-.37,1.10),.048,'metal')
    rod('Handlebar',(-.36,-.37,1.10),(.36,-.37,1.10),.035,'metal')
    for x in [-.34,.34]: rod('Grip',(x-.065,-.37,1.10),(x+.065,-.37,1.10),.05,'navy')
    for side in [-1,1]:
        cube('Foot deck',(side*width*.78,.27,.55),(.15,length*.46,.055),'navy',.025)
        for i in range(7): cube('Deck tread',(side*width*.78,-.25+i*.14,.589),(.14,.025,.018),'metal',.005)
        rod('Side highlight',(side*width*.82,-.5,.51),(side*width*.80,.70,.51),.025,'white')
    torus('Jet outlet',(0,length*.47,.31),.12,.035,'metal',(math.pi/2,0,0))
    cube('Rear step',(0,length*.48,.49),(.56,.16,.05),'navy',.02)
    text('Hull badge','HD',(0,-length*.29,.89),.14,'white',(.3,0,0))
    for n,p in [('rider_mount',(0,.25,.91)),('handlebar_mount',(0,-.37,1.1)),('wake_emitter',(0,length*.5,.23))]:
        o=bpy.data.objects.new(n,None); current.objects.link(o); o.location=p
    finish(name,'watercraft','Forward is -Y; Z up; metric units; named rider, handlebar and wake attachment markers.')
craft('01_Needle_Agile','teal',.48,2.65)
craft('02_Surge_Balanced','orange',.57,2.9)
craft('03_Leviathan_Power','purple',.67,3.15)

def prop(name,category,fn):
    start(name,category); fn(); finish(name,category)
def palm():
    for i in range(7): rod('Trunk segment',(.06*i,0,i*.42),(.06*(i+1),0,(i+1)*.42),.15-i*.009,'brown',.14-i*.009)
    for i in range(8):
        a=i*math.tau/8; ux,uy=math.cos(a),math.sin(a); x=.42
        mesh('Palm frond',[(x,0,2.96),(x+ux*.8-uy*.20,uy*.8+ux*.20,3.22),(x+ux*1.65,uy*1.65,2.65),(x+ux*.8+uy*.20,uy*.8-ux*.20,3.22)],[(0,1,2,3)],'leaf')
    for x in [.28,.46,.57]: uv('Coconut',(x,-.1,2.87),(.13,)*3,'brown')
prop('Palm_tree','sunbeam',palm)
def rock(color='rock'):
    for i in range(3):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(i*.45,0,.3+i*.12)); o=bpy.context.object; o.scale=(.6,.55,.45+i*.1); add(o,'Rock',color)
prop('Coastal_rocks','shared',rock)
prop('Ice_cluster','glacier',lambda:rock('ice'))
def dock():
    for i in range(12): cube('Deck board',(0,i*.25,1),(2,.23,.10),'tan',.015)
    for x in [-.85,.85]:
        for y in [0,2.7]: rod('Pile',(x,y,-.5),(x,y,1.35),.10,'brown')
prop('Dock_3m','sunbeam',dock)
def buoy():
    uv('Buoy body',(0,0,.2),(.35,.35,.45),'orange'); torus('Reflective band',(0,0,.28),.32,.035,'white')
    rod('Flag pole',(0,0,.5),(0,0,1.35),.025,'metal'); mesh('Flag',[(0,0,1.35),(.5,0,1.22),(0,0,1.02)],[(0,1,2)],'teal')
prop('Course_buoy','race',buoy)
def arch():
    for x in [-3,3]:
        rod('Arch pillar',(x,0,0),(x,0,3.5),.23,'teal'); uv('Float',(x,0,.12),(.7,.6,.3),'orange')
    cube('Header',(0,0,3.45),(6.5,.45,.65),'navy',.18); text('Start title','HYDRO DRIFT',(0,-.24,3.3),.43,'white')
    for x in [-2.4,-2,-1.6,1.6,2,2.4]: cube('Race checker',(x,-.24,3.63),(.2,.015,.17),'yellow',.0)
prop('Start_finish_arch','race',arch)
def ramp():
    mesh('Ramp', [(-1,-2,0),(1,-2,0),(-1,2,0),(1,2,0),(-1,2,1),(1,2,1)],[(0,1,3,2),(0,4,5,1),(2,3,5,4),(0,2,4),(1,5,3)],'teal')
    for x in [-.86,.86]: rod('Ramp edge',(x,-2,.04),(x,2,1.04),.035,'yellow')
prop('Jump_ramp','race',ramp)
def sign():
    cube('Sign',(0,0,1.3),(1.6,.12,.75),'navy'); text('Arrow','>>>',(0,-.07,1.15),.45,'yellow')
    for x in [-.6,.6]: rod('Post',(x,0,0),(x,0,1.2),.05,'metal')
prop('Direction_sign','race',sign)
def container():
    cube('Container',(0,0,1.2),(2.4,5,2.4),'blue')
    for x in [-1.22,1.22]:
        for i in range(17): cube('Corrugation',(x,-2.3+i*.28,1.2),(.045,.055,2.2),'teal',.015)
    text('Cargo label','HYDRO\nFREIGHT',(0,-2.55,1.35),.35,'white')
prop('Shipping_container','neon',container)
def building():
    cube('Harbor tower',(0,0,3),(3,3,6),'navy',.12)
    for z in [1,2,3,4,5]:
        for x in [-.95,0,.95]: cube('Lit window',(x,-1.51,z),(.48,.03,.55),'glow',.03)
    text('Neon sign','DRIFT',(0,-1.56,5.8),.5,'pink')
prop('Harbor_building','neon',building)
def mangrove():
    rod('Trunk',(0,0,.5),(0,0,3.2),.22,'brown',.13)
    for i in range(6):
        a=i*math.tau/6; rod('Stilt root',(0,0,1.4),(math.cos(a),math.sin(a),0),.08,'brown',.04)
        uv('Canopy',(math.cos(a)*.6,math.sin(a)*.6,3.2),(.9,.8,.55),'green')
prop('Mangrove_tree','mangrove',mangrove)
def ruin():
    for x in [-1.4,1.4]:
        for i in range(5): cube('Ancient block',(x,0,.25+i*.5),(.65,.75,.47),'rock',.06)
    cube('Lintel',(0,0,2.7),(3.5,.9,.55),'rock',.09)
    for x in [-1.2,0,1.2]: cube('Moss',(x,-.1,3.0),(.6,.6,.06),'green',.02)
prop('Ruins_arch','mangrove',ruin)
def iceberg():
    for i in range(4):
        bpy.ops.mesh.primitive_cone_add(vertices=5,radius1=.8,radius2=.15,depth=1.8+i*.3,location=(i*.55,0,.5+i*.15)); add(bpy.context.object,'Ice pinnacle','ice')
prop('Iceberg','glacier',iceberg)
def lighthouse():
    for i in range(5): rod('Painted tower',(0,0,i*.7),(0,0,(i+1)*.7),.55-i*.04,'white' if i%2==0 else 'orange',.51-i*.04)
    rod('Lantern',(0,0,3.5),(0,0,4),.36,'glow'); rod('Roof',(0,0,4),(0,0,4.3),.55,'navy',0)
    torus('Gallery',(0,0,3.5),.6,.055,'metal')
prop('Lighthouse','stormbreak',lighthouse)
def volcano():
    rod('Volcanic cone',(0,0,0),(0,0,2.8),3,'rock',.65); torus('Crater rim',(0,0,2.8),.66,.13,'navy'); uv('Lava pool',(0,0,2.79),(.57,.57,.025),'lava')
    for i in range(3): rod('Lava channel',(.55+i*.07,-.2,2.7),(1.8+i*.10,-.65,.6),.05,'lava')
prop('Volcano','ember',volcano)
def geyser():
    rock(); torus('Vent',(0,0,.6),.3,.12,'navy'); uv('Hot pool',(0,0,.55),(.3,.3,.035),'lava')
prop('Geyser_vent','ember',geyser)
def boat():
    uv('Boat hull',(0,0,.35),(.7,1.6,.4),'white'); cube('Cabin',(0,.25,.85),(1,1.2,.85),'teal',.16); cube('Windshield',(0,-.37,1.05),(.8,.03,.35),'glass',.04)
    rod('Mast',(0,.4,1.3),(0,.4,2),.025,'metal')
prop('Harbor_boat','shared',boat)
def umbrella():
    rod('Umbrella pole',(0,0,0),(0,0,2.3),.045,'white')
    for i in range(8):
        a=i*math.tau/8;b=(i+1)*math.tau/8
        mesh('Canopy panel',[(0,0,2.55),(math.cos(a),math.sin(a),2.12),(math.cos(b),math.sin(b),2.12)],[(0,1,2)],'orange' if i%2 else 'white')
prop('Beach_umbrella','sunbeam',umbrella)
def barrier():
    for i in range(5): uv('Floating segment',(i*.45,0,.1),(.24,.17,.16),'orange' if i%2==0 else 'white')
prop('Floating_barrier','race',barrier)
def pickup(kind):
    torus('Pickup ring',(0,0,.7),.37,.055,'yellow',(math.pi/2,0,0))
    if kind=='battery':
        cube('Battery',(0,0,.7),(.25,.2,.48),'teal'); cube('Terminal',(0,0,.98),(.1,.1,.08),'metal'); text('Charge','+',(0,-.12,.61),.24,'white')
    elif kind=='shield': uv('Shield',(0,0,.7),(.25,.1,.3),'blue')
    elif kind=='pulse':
        for z in [.55,.7,.85]: torus('Wave',(0,0,z),.2,.027,'glow')
    else:
        for i in range(5): torus('Whirlpool',(0,0,.48+i*.08),.08+i*.04,.025,'purple')
for kind in ['battery','shield','pulse','whirlpool']: prop('Pickup_'+kind,'items',lambda k=kind:pickup(k))
def trophy():
    cube('Plinth',(0,0,.12),(.6,.6,.24),'navy'); rod('Stem',(0,0,.24),(0,0,.6),.1,'yellow'); uv('Cup',(0,0,.83),(.3,.25,.3),'yellow')
    for x in [-.3,.3]: torus('Handle',(x,0,.87),.16,.04,'yellow',(math.pi/2,0,0))
prop('Championship_trophy','race',trophy)

# A tiled mesh preview is supplied; runtime water shaders/physics belong in the engine.
def water():
    N=32; verts=[(-8+16*x/N,-8+16*y/N,.06*math.sin(x*.55+y*.32)) for y in range(N+1) for x in range(N+1)]
    faces=[(y*(N+1)+x,y*(N+1)+x+1,(y+1)*(N+1)+x+1,(y+1)*(N+1)+x) for y in range(N) for x in range(N)]
    o=mesh('Water surface',verts,faces,'teal')
    for p in o.data.polygons:p.use_smooth=True
prop('Water_tile_16m','shared',water)

scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.render.engine='CYCLES'; scene.cycles.samples=16
scene.cycles.use_denoising=True; scene.render.resolution_x=1600; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
scene.world.color=(.18,.18,.18)
scene.view_settings.view_transform='AgX'
stage=start('Presentation','preview')
cube('Studio floor',(0,0,-.15),(40,32,.2),'navy',.02)
def aim(o,p): o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Key',(-5,-8,12),2200,9),('Fill',(7,-2,8),1600,8),('Rim',(0,6,9),2400,7)]:
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.shape='DISK'; d.size=size; o=bpy.data.objects.new(name,d); stage.objects.link(o); o.location=loc; aim(o,(0,0,1))
d=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',d); stage.objects.link(cam); scene.camera=cam; cam.data.type='ORTHO'
def show(names,positions):
    for c in bpy.data.collections:
        if c.name!='Presentation': c.hide_render=True; c.hide_viewport=True
    # Instance source collections; exported models remain at their origin.
    for o in list(stage.objects):
        if o.instance_type=='COLLECTION' or o.name.startswith('Label'): bpy.data.objects.remove(o,do_unlink=True)
    for name,p in zip(names,positions):
        c=bpy.data.collections[name]; c.hide_render=False; c.hide_viewport=False
        # originals moved out of camera; instance offset compensates for source placement
        c.hide_render=True
        inst=bpy.data.objects.new(name+'_display',None); stage.objects.link(inst); inst.instance_type='COLLECTION'; inst.instance_collection=c; inst.location=p
    # Collection hide_render also affects instances: use layer exclusion for sources instead.
    for c in bpy.data.collections:
        if c.name not in ['Presentation','Collection']:
            c.hide_render=False; c.hide_viewport=False
            lc=scene.view_layers[0].layer_collection.children.get(c.name)
            if lc: lc.exclude=True
    for name,p in zip(names,positions): text('Label_'+name,name.replace('_',' '),(p[0],p[1]-.50,.02),.20,'white',(0,0,0))
def render(name,loc,target,scale):
    cam.location=loc; aim(cam,target); cam.data.ortho_scale=scale; scene.render.filepath=str(ROOT/'previews'/name); bpy.ops.render.render(write_still=True)
show([x['name'] for x in catalog if x['category']=='character'],[(x*1.65-5.775,0,0) for x in range(8)])
text('Label_title','HYDRO DRIFT / RIDER LINEUP',(0,-2.1,.02),.40,'teal',(0,0,0))
render('01_characters.png',(2,-14,8),(0,-.2,.8),14.5)
show([x['name'] for x in catalog if x['category']=='watercraft'],[(-2.5,0,0),(0,0,0),(2.5,0,0)])
render('02_watercraft.png',(6,-9,8),(0,0,.5),10)
names=[x['name'] for x in catalog if x['category'] not in ['character','watercraft'] and x['name']!='Water_tile_16m']
show(names,[((i%6)*5-12.5,(i//6)*6,0) for i in range(len(names))])
render('03_environment_library.png',(23,-32,34),(0,10,1),39)
scene.render.resolution_x=1600; scene.render.resolution_y=1000
# Save the collection library with a usable craft presentation and all original sources preserved.
show(['01_Needle_Agile','02_Surge_Balanced','03_Leviathan_Power'],[(-2.5,0,0),(0,0,0),(2.5,0,0)])
cam.location=(6,-9,8); aim(cam,(0,0,.5)); cam.data.ortho_scale=10
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source'/'Hydro_Drift_Library.blend'),compress=True)
(ROOT/'manifest.json').write_text(json.dumps({'units':'meters','forward':'-Y','up':'Z','assets':catalog},indent=2))
print('HYDRO_ASSETS_COMPLETE',len(catalog),flush=True)
