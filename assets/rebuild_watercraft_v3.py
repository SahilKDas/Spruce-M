"""Hydro Drift: shaped hulls, fitted fairings, saddle upholstery and mechanical details."""
import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from surface_modeling import *
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
def material(name,c,rough=.4,metal=0,coat=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Coat Weight'].default_value=coat
    return m
M={k:material(k,c,r,m,coat) for k,c,r,m,coat in [('Navy hull',(.016,.023,.037),.29,.25,.30),('Needle teal',(.008,.43,.36),.24,.28,.40),('Surge orange',(.88,.21,.027),.26,.22,.40),('Leviathan blue',(.035,.19,.44),.25,.28,.4),('Ivory panels',(.72,.77,.73),.34,.1,.25),('Rubber',(.009,.013,.018),.67,0,0),('Seat',(.027,.035,.044),.52,0,.08),('Brushed alloy',(.28,.34,.37),.28,.88,.1),('Glass',(.004,.017,.021),.17,.20,.45),('Display',(.014,.72,.51),.35,.2,.1)]}
M['Display'].node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(.005,.28,.18,1)
M['Display'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.4
catalog=[]
def strip(name,col,points,radius,mat,flat=1,sub=1):
    s=Surface(name);sweep(s,points,[radius]*len(points),0,segments=12,flat=flat);return s.obj(col,[mat],sub)
def word(col,text,position,rotation,size,mat):
    curve=bpy.data.curves.new(text,'FONT');curve.body=text;curve.size=size;curve.align_x='CENTER';curve.extrude=.0005
    obj=bpy.data.objects.new(text,curve);col.objects.link(obj);obj.location=position;obj.rotation_euler=rotation;curve.materials.append(mat)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH');obj.select_set(False)
    return obj

for number,(name,color,beam,length) in enumerate([('01_Needle_Agile','Needle teal',.97,3.02),('02_Surge_Balanced','Surge orange',1.04,3.12),('03_Leviathan_Power','Leviathan blue',1.12,3.22)]):
    col=bpy.data.collections.new(name);scene.collection.children.link(col);paint=M[color]
    def width(t):return beam*profile([(0,.33),(.10,.40),(.32,.455),(.55,.44),(.70,.37),(.86,.245),(.95,.115),(1,.006)],t)
    def ycoord(t):return 1.45-length*t
    def deck_height(x,y):
        t=clamp((1.45-y)/length);v=math.sqrt(max(.001,1-(x/max(.01,width(t)))**2))
        z=.305+.065*gauss(t,.93,.18)+.20*v+.13*gauss(t,.65,.17)*v**3
        z-=.025*gauss(abs(x),.32*beam,.067)*gauss(y,.35,.85)
        return z
    s=Surface('Continuous planing hull');rows=[]
    for i in range(81):
        t=i/80;w=width(t);row=[]
        for j in range(96):
            a=TAU*j/96;c=math.cos(a);v=math.sin(a)
            x=w*c*(1-.17*max(0,-v));z=.305+.065*gauss(t,.93,.18)+(.20 if v>0 else .19)*v
            # Continuous concave channels and chines along the running surface.
            if v<0:z+=.018*gauss(abs(c),.69,.09)*(1-t)*(-v)
            else:z=deck_height(x,ycoord(t))
            row.append(s.vertex((x,ycoord(t),z)))
        rows.append(row)
    for i in range(80):
        for j in range(96):s.face((rows[i][j],rows[i][(j+1)%96],rows[i+1][(j+1)%96],rows[i+1][j]),1 if j<48 else 0)
    s.cap(rows[0]);s.cap(rows[-1],1);hull=s.obj(col,[M['Navy hull'],paint],2)
    # The gunwale follows the sheer line and is a separately fitted rubber molding.
    for side in [-1,1]:
        points=[(side*width(i/80),ycoord(i/80),.305+.065*gauss(i/80,.93,.18)) for i in range(81)]
        strip('Continuous rub rail',col,points,.014,M['Rubber'],flat=.7,sub=1)
        points=[(side*width(i/80)*.987,ycoord(i/80),.35+.063*gauss(i/80,.93,.18)) for i in range(81)]
        strip('Paint reveal',col,points,.0035,M['Ivory panels'],flat=.7,sub=1)
    # The sculpted deck is part of the hull surface; no overlapping upper shell.
    # Foot wells have recessed, diamond-ribbed mats on both sides of the saddle.
    for side in [-1,1]:
        s=Surface('Molded footwell');rows=[]
        for i in range(45):
            t=i/44;y=1.14-1.58*t;row=[]
            for j in range(13):
                u=-1+2*j/12;x=side*(.321*beam+.065*beam*u)
                z=deck_height(x,y)+.008+.0027*math.sin(t*80+u*7)*math.sin(t*80-u*7)
                row.append(s.vertex((x,y,z)))
            rows.append(row)
        for i in range(44):
            for j in range(12):s.face((rows[i][j],rows[i][j+1],rows[i+1][j+1],rows[i+1][j]))
        obj=s.obj(col,[M['Rubber']],1);solid=obj.modifiers.new('Inset mat edge','SOLIDIFY');solid.thickness=.015
        strip('Footwell drainage channel',col,[(side*.247*beam,1.17-i/32*1.55,deck_height(side*.247*beam,1.17-i/32*1.55)+.004) for i in range(33)],.007,M['Ivory panels'],sub=1)
    # Fitted saddle: changing cross sections, recessed upholstery channels, double piping.
    s=Surface('Ergonomic saddle');rows=[]
    for i in range(57):
        t=i/56;y=1.12-1.38*t;rx=profile([(0,.12),(.12,.195),(.37,.17),(.60,.14),(.85,.113),(1,.071)],t)
        center=profile([(0,.66),(.20,.735),(.42,.705),(.72,.735),(1,.78)],t)
        row=[]
        for j in range(64):
            a=TAU*j/64;v=math.sin(a);z=center+.067*v
            if v>0:z+=.0028*math.cos(t*math.pi*34)*v*v
            row.append(s.vertex((rx*math.cos(a),y,z)))
        rows.append(row)
    for i in range(56):
        for j in range(64):s.face((rows[i][j],rows[i][(j+1)%64],rows[i+1][(j+1)%64],rows[i+1][j]))
    s.cap(rows[0]);s.cap(rows[-1]);s.obj(col,[M['Seat']],2)
    for side in [-1,1]:
        points=[]
        for i in range(57):
            t=i/56;rx=profile([(0,.12),(.12,.195),(.37,.17),(.60,.14),(.85,.113),(1,.071)],t)
            center=profile([(0,.66),(.20,.735),(.42,.705),(.72,.735),(1,.78)],t)
            points.append((side*rx*.94,1.12-1.38*t,center+.020))
        strip('Saddle double stitch',col,points,.0018,M['Ivory panels'],sub=1)
    # Steering cowling, connected profile rings with a sloped instrument panel.
    s=Surface('Steering console');loft(s,[((0,y,z),rx,rz,{}) for y,z,rx,rz in [(-.08,.65,.09,.04),(-.15,.70,.16,.10),(-.27,.77,.20,.16),(-.40,.78,.205,.20),(-.55,.70,.17,.15),(-.63,.63,.095,.07),(-.65,.61,.01,.01)]],48,axis='Y');s.obj(col,[paint],2)
    s=Surface('Instrument glass');s.v=[(-.115,-.32,.985),(.115,-.32,.985),(.103,-.48,.970),(-.103,-.48,.970)];s.w=[{}]*4;s.face((0,1,2,3));glass=s.obj(col,[M['Glass']]);solid=glass.modifiers.new('Glass thickness','SOLIDIFY');solid.thickness=.007;bevel=glass.modifiers.new('Instrument rim','BEVEL');bevel.width=.015;bevel.segments=4
    word(col,'HD  07',(0,-.382,.994),(0,0,0),.052,M['Display'])
    bar=[(-.405,-.38,1.10),(-.30,-.42,1.10),(-.19,-.465,1.06),(0,-.45,1.035),(.19,-.465,1.06),(.30,-.42,1.10),(.405,-.38,1.10)]
    strip('Swept handlebar',col,bar,.020,M['Brushed alloy'],sub=2)
    strip('Steering stem',col,[(0,-.43,.91),(0,-.45,.97),(0,-.45,1.035)],.029,M['Navy hull'],sub=2)
    for side in [-1,1]:
        s=Surface('Diamond grip');prev=None
        for i in range(45):
            t=i/44;x=side*(.275+t*.14);y=-.425+t*.054
            r=.026+.0018*math.cos(t*TAU*14)
            loop=s.ring([(x,y+r*math.cos(TAU*j/32),1.10+r*math.sin(TAU*j/32)) for j in range(32)])
            if prev is None:s.cap(loop)
            else:s.bridge(prev,loop)
            prev=loop
        s.cap(prev);s.obj(col,[M['Rubber']],1)
        strip('Brake lever',col,[(side*.255,-.47,1.086),(side*.31,-.48,1.078),(side*.39,-.46,1.08)],.006,M['Brushed alloy'],flat=.5,sub=2)
        # Recessed intake slots with shaped lips, not painted circles.
        for j in range(5):
            y=-.40-j*.072;t=(1.45-y)/length;x=side*width(t)*.82;z=.47+.052*(4-j)/4
            points=[(x,y-d,deck_height(x,y-d)+.006) for d in [0,.025,.05]]
            strip('Intake recess',col,points,.010,M['Rubber'],flat=.22,sub=2)
            strip('Intake lip',col,[(p[0]+side*.011,p[1],deck_height(p[0]+side*.011,p[1])+.008) for p in points],.0025,M['Brushed alloy'],flat=.6,sub=1)
    # Hollow waterjet with a rolled lip and internal guide vanes.
    s=Surface('Waterjet outlet');prev=None
    for y,r in [(1.28,.081),(1.40,.108),(1.49,.12),(1.51,.123),(1.525,.118),(1.51,.099),(1.44,.092),(1.29,.065)]:
        loop=s.ring([(r*math.cos(TAU*j/64),y,.245+r*math.sin(TAU*j/64)) for j in range(64)])
        if prev is not None:s.bridge(prev,loop)
        prev=loop
    s.cap(prev);s.obj(col,[M['Brushed alloy']],2)
    for a in [0,math.pi/2,math.pi,3*math.pi/2]:
        strip('Jet stator vane',col,[(.017*math.cos(a),1.39,.245+.017*math.sin(a)),(.085*math.cos(a),1.37,.245+.085*math.sin(a))],.005,M['Navy hull'],flat=.4,sub=1)
    # Rear boarding step and grab handle are part of the functional silhouette.
    strip('Boarding handle',col,[(-.23,1.16,.59),(-.26,1.31,.56),(0,1.38,.54),(.26,1.31,.56),(.23,1.16,.59)],.021,M['Rubber'],sub=2)
    label=word(col,'HYDRO / '+str(number+1).zfill(2),(0,-1.0,.70),(0,0,math.pi),.066,M['Ivory panels'])
    wrap=label.modifiers.new('Conform branding to bow','SHRINKWRAP');wrap.target=hull;wrap.wrap_method='NEAREST_SURFACEPOINT';wrap.offset=.002
    count=sum(triangles(o) for o in col.objects if o.type=='MESH')
    col['source_triangles']=count;col['construction']='Continuous lofted hull; fitted fairings; upholstered saddle; modeled intake, tread, cockpit and hollow waterjet'
    catalog.append({'name':name,'source_triangles':count,'components':'Manufactured parts are separate fitted meshes; hull is one continuous shell'})
    print('V3_CRAFT',catalog[-1],flush=True)
    col.hide_render=True

# Studio setup, without primitive modeling operators.
studio=bpy.data.collections.new('Craft_Studio');scene.collection.children.link(studio)
s=Surface('Floor');s.v=[(-100,-100,0),(100,-100,0),(100,100,0),(-100,100,0)];s.w=[{}]*4;s.face((0,1,2,3));s.obj(studio,[material('Studio slate',(.045,.061,.07),.85)])
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for label,loc,power,size in [('Key',(-3,-4,6),950,5),('Fill',(4,-1,4),700,4),('Rim',(1,4,5),1100,3)]:
    d=bpy.data.lights.new(label,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(label,d);studio.objects.link(o);o.location=loc;aim(o,(0,0,.4))
world=bpy.data.worlds.new('Studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.17,.19,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;scene.world=world
d=bpy.data.cameras.new('Craft_review');cam=bpy.data.objects.new('Craft_review',d);studio.objects.link(cam);cam.location=(3,-4,3);aim(cam,(0,-.08,.5));d.type='ORTHO';d.ortho_scale=3.8;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True;scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
bpy.data.collections['01_Needle_Agile'].hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Watercraft_v3.blend'),compress=True)
(ROOT/'watercraft_v3.json').write_text(json.dumps(catalog,indent=2))
scene.render.filepath=str(ROOT/'previews/16_v3_watercraft.png');bpy.ops.render.render(write_still=True)
print('V3_WATERCRAFT_READY',flush=True)
