"""Surface-built tropical scenery and course equipment for Hydro Drift."""
import bpy,math,sys,json,random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from surface_modeling import *
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
def material(name,c,rough=.6,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
M={k:material(k,c,r,m) for k,c,r,m in [('Bark',(.24,.14,.07),.9,0),('Leaf',(.043,.19,.06),.7,0),('Leaf light',(.12,.32,.055),.7,0),('Rock',(.20,.24,.25),.91,0),('Rock warm',(.26,.25,.22),.93,0),('Sand',(.65,.49,.26),.88,0),('Grass',(.11,.23,.065),.85,0),('Orange',(.91,.20,.023),.35,.1),('White',(.80,.84,.76),.45,.05),('Navy',(.02,.033,.05),.4,.2),('Rubber',(.012,.017,.022),.75,0),('Wood',(.35,.20,.093),.84,0),('Wood light',(.41,.26,.13),.8,0),('Metal',(.34,.40,.42),.32,.85),('Yellow',(.95,.60,.025),.4,.1)]}
catalog=[]
def collection(name):c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
def path(name,col,points,radii,mat,segments=12,sub=1,flat=1):
    s=Surface(name);sweep(s,points,radii,0,segments=segments,flat=flat);return s.obj(col,[M[mat]],sub)
def finish(col):
    count=sum(triangles(o) for o in col.objects if o.type=='MESH');catalog.append({'name':col.name,'source_triangles':count});print('V3_PROP',catalog[-1],flush=True)

col=collection('Palm_tree')
s=Surface('Curved ringed palm trunk');prev=None
for i in range(81):
    t=i/80;z=t*3.8;cx=.22*t*t;cy=.07*math.sin(t*2.3);r=.15-.075*t+.013*math.cos(t*TAU*24)**5
    loop=s.ring([(cx+r*(1+.04*math.cos(a*5+t*12))*math.cos(a),cy+r*math.sin(a),z) for a in [TAU*j/40 for j in range(40)]])
    if prev is None:s.cap(loop)
    else:s.bridge(prev,loop)
    prev=loop
s.cap(prev);s.obj(col,[M['Bark']],1)
for leaf in range(13):
    a=leaf/13*TAU;reach=1.6+.25*math.sin(leaf*8);start=Vector((.22,.065,3.72));forward=Vector((math.cos(a),math.sin(a),0));side=Vector((-math.sin(a),math.cos(a),0))
    def center(t):return start+forward*reach*t+Vector((0,0,.55*math.sin(t*math.pi*.9)-.82*t*t))
    path('Frond rachis',col,[center(i/24) for i in range(25)],[.014*(1-i/26) for i in range(25)],'Leaf light',8,1)
    s=Surface('Curved pinnate leaflets')
    for k in range(1,21):
        t=k/22;base=center(t);length=.37*math.sin(math.pi*t)**.6
        for sign in [-1,1]:
            rows=[]
            for i in range(9):
                u=i/8;p=base+side*sign*length*u+forward*.14*u+Vector((0,0,-.10*u*u))
                width=.032*math.sin(math.pi*u)**.65+.001
                rows.append(s.ring([p-forward*width+Vector((0,0,-.008*math.sin(math.pi*u))),p+Vector((0,0,.012*math.sin(math.pi*u))),p+forward*width+Vector((0,0,-.008*math.sin(math.pi*u)))]))
            for i in range(8):
                for j in range(2):s.face((rows[i][j],rows[i][j+1],rows[i+1][j+1],rows[i+1][j]),leaf%2)
    s.obj(col,[M['Leaf'],M['Leaf light']],1)
finish(col)

col=collection('Coastal_rocks')
for rock,(cx,cy,sx,sy,sz) in enumerate([(0,0,.73,.65,1.17),(.8,.18,.50,.48,.78),(-.51,.21,.41,.42,.54)]):
    s=Surface('Weathered coastal stone');prev=None
    for i in range(49):
        t=i/48;z=-.1+sz*t;ring=[]
        for j in range(80):
            a=TAU*j/80;shape=(.52+.48*math.sin(math.pi*t)**.55)*(1-.96*clamp((t-.82)/.18)**2)
            erosion=.075*math.sin(a*3+t*8+rock)+.05*math.cos(a*7-t*6)+.023*math.sin(a*13+t*23)+.009*math.sin(a*31+t*49)
            radius=shape*(1+erosion)
            ring.append((cx+sx*radius*math.cos(a)+.10*t*t,cy+sy*radius*math.sin(a),z+.018*math.sin(a*7+t*9)*math.sin(math.pi*t)))
        loop=s.ring(ring)
        if prev is None:s.cap(loop)
        else:s.bridge(prev,loop)
        prev=loop
    s.cap(prev);s.obj(col,[M['Rock' if rock%2==0 else 'Rock warm']],1)
finish(col)

col=collection('Course_buoy');s=Surface('Molded striped navigation buoy');prev=None
sections=[(-.12,.26),(-.09,.38),(-.055,.43),(.015,.43),(.055,.37),(.09,.32),(.20,.30),(.25,.29),(.28,.285),(.43,.26),(.46,.255),(.52,.25),(.63,.22),(.67,.19),(.68,.07),(.72,.045)]
for z,r in sections:
    loop=s.ring([(r*math.cos(TAU*j/48),r*math.sin(TAU*j/48),z) for j in range(48)])
    if prev is None:s.cap(loop)
    else:s.bridge(prev,loop,1 if .25<=z<=.46 else (2 if z<.055 else 0))
    prev=loop
s.cap(prev);s.obj(col,[M['Orange'],M['White'],M['Rubber']],2)
path('Buoy lifting eye',col,[(.055*math.cos(TAU*j/32),0,.737+.055*math.sin(TAU*j/32)) for j in range(33)],[.009]*33,'Metal',8,1)
finish(col)

col=collection('Beach_umbrella');s=Surface('Tensioned eight-panel canopy');rows=[]
for i in range(33):
    t=max(.002,i/32);row=[]
    for j in range(128):
        a=TAU*j/128;between=abs(math.sin(a*4));r=1.1*t*(1-.035*between*t*t)
        z=2.45-.49*t**1.4-.06*between*t*t
        row.append(s.vertex((r*math.cos(a),r*math.sin(a),z)))
    rows.append(row)
for i in range(32):
    for j in range(128):s.face((rows[i][j],rows[i][(j+1)%128],rows[i+1][(j+1)%128],rows[i+1][j]),(j//16)%2)
s.cap(rows[0]);s.obj(col,[M['Orange'],M['White']],1)
path('Umbrella pole',col,[(0,0,z) for z in [0,.03,2.35,2.42]],[.018,.018,.017,.012],'Metal',24,1)
for j in range(8):
    a=TAU*j/8;path('Canopy rib',col,[(1.1*t*math.cos(a),1.1*t*math.sin(a),2.434-.49*t**1.4) for t in [i/16 for i in range(17)]],[.004]*17,'Metal',8,1)
finish(col)

col=collection('Dock_3m')
for board in range(13):
    s=Surface('Weathered deck plank');prev=None
    for i in range(29):
        u=i/28;x=-.92+1.84*u;cy=-1.4+board*.23;pts=[]
        for j in range(16):
            a=TAU*j/16;y=cy+.108*math.copysign(abs(math.cos(a))**.25,math.cos(a));z=.20+.042*math.copysign(abs(math.sin(a))**.25,math.sin(a))
            z+=.0009*math.sin(x*32+a*9)+.002*math.sin(x*4+board)
            pts.append((x,y,z))
        loop=s.ring(pts)
        if prev is None:s.cap(loop)
        else:s.bridge(prev,loop)
        prev=loop
    s.cap(prev);s.obj(col,[M['Wood' if board%3 else 'Wood light']],1)
for x in [-.75,.75]:
    for y in [-1.23,1.23]:
        s=Surface('Dock piling');loft(s,[((x,y,z),r,r,{}) for z,r in [(-.7,.07),(-.67,.075),(.7,.065),(.75,.06)]],20);s.obj(col,[M['Wood']],1)
        for z in [.29,.65]:path('Piling rope wrap',col,[(x+.075*math.cos(TAU*j/32),y+.075*math.sin(TAU*j/32),z) for j in range(33)],[.01]*33,'Navy',8,1)
finish(col)

col=collection('Jump_ramp');s=Surface('Traction ramp deck');rows=[]
for iy in range(81):
    t=iy/80;y=4-8*t;row=[]
    for ix in range(41):
        u=-1+2*ix/40;x=2.5*u;z=.035+1.365*t
        z+=.013*max(0,math.cos(t*TAU*31+abs(u)*5))**6
        row.append(s.vertex((x,y,z)))
    rows.append(row)
for i in range(80):
    for j in range(40):s.face((rows[i][j],rows[i][j+1],rows[i+1][j+1],rows[i+1][j]),1 if j<3 or j>36 else 0)
obj=s.obj(col,[M['Navy'],M['Yellow']],1);mod=obj.modifiers.new('Ramp deck thickness','SOLIDIFY');mod.thickness=.05
for side in [-1,1]:
    s=Surface('Riveted side girder');x=side*2.44;s.v=[(x,4,0),(x,-4,0),(x,-4,1.4),(x,4,.03),(x+side*.08,4,0),(x+side*.08,-4,0),(x+side*.08,-4,1.4),(x+side*.08,4,.03)];s.w=[{}]*8
    for face in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]:s.face(face)
    o=s.obj(col,[M['Orange']]);m=o.modifiers.new('Girder edge bevel','BEVEL');m.width=.02;m.segments=3
    for i in range(17):
        y=3.6-i*.45;z=.04+(4-y)/8*1.365
        path('Rivet',col,[(x+side*.085,y,z-.015),(x+side*.09,y,z-.015)],[.016,.012],'Metal',12,0)
finish(col)

col=collection('Sunbeam_Island');s=Surface('Eroded shoreline terrain');rows=[]
for i in range(81):
    r=.001+1.18*i/80;row=[]
    for j in range(192):
        a=TAU*j/192;coast=1+.018*math.sin(a*7)+.010*math.sin(a*13)
        x=54*r*math.cos(a)*coast;y=83*r*math.sin(a)*coast
        z=profile([(0,2.65),(.40,2.5),(.65,1.8),(.82,.9),(.95,.20),(1,-.08),(1.18,-1.0)],r)
        z+=(.20*math.sin(x*.18)*math.cos(y*.13)+.11*math.sin(x*.51+y*.27))*(1-clamp((r-.8)/.22))
        row.append(s.vertex((x,y,z)))
    rows.append(row)
for i in range(80):
    for j in range(192):
        a=TAU*j/192;r=1.18*i/80;mat=0 if r>.765+.015*math.sin(a*9) else 1
        s.face((rows[i][j],rows[i][(j+1)%192],rows[i+1][(j+1)%192],rows[i+1][j]),mat)
s.cap(rows[0],1);s.obj(col,[M['Sand'],M['Grass']],1);finish(col)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Environment_v3.blend'),compress=True)
(ROOT/'environment_v3.json').write_text(json.dumps(catalog,indent=2))
print('V3_ENVIRONMENT_READY',flush=True)
