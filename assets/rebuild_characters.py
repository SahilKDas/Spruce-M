"""Hydro Drift anatomical rider revision: skinned limbs, static fingers, IK rigs.
Blender 5.1 background script. Original geometry; no downloaded assets.
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.unit_settings.system='METRIC';scene.render.fps=30
scene.world=bpy.data.worlds.new('Studio world');scene.world.color=(.12,.12,.12)
M={}
def material(n,c,rough=.45,metal=0):
    m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;M[n]=m;return m
for n,c,r,m in [('navy',(.013,.023,.044),.56,0),('rubber',(.018,.022,.027),.7,0),('teal',(.008,.42,.36),.43,0),('orange',(.95,.21,.026),.48,0),('white',(.8,.85,.82),.42,0),('yellow',(.95,.59,.035),.4,0),('blue',(.05,.23,.45),.43,0),('purple',(.25,.075,.43),.46,0),('pink',(.71,.14,.29),.46,0),('skin_kai',(.53,.27,.16),.52,0),('skin_zuri',(.25,.105,.058),.5,0),('lip_kai',(.35,.12,.085),.48,0),('lip_zuri',(.15,.046,.027),.48,0),('hair',(.028,.018,.013),.8,0),('brown',(.24,.10,.04),.75,0),('tan',(.47,.28,.13),.69,0),('muzzle',(.57,.40,.24),.68,0),('metal',(.20,.27,.30),.3,.8),('glass',(.024,.067,.086),.19,.45),('iris',(.045,.09,.075),.32,0),('eye',(.55,.60,.57),.31,0),('black',(.003,.004,.005),.3,0)]:material(n,c,r,m)
# A shared embedded woven normal map adds material detail without large textures.
im=bpy.data.images.new('Woven_neoprene_normal_256',256,256,alpha=False)
px=[]
for y in range(256):
    for x in range(256):
        px.extend((.5+.09*math.sin(x*math.pi/2),.5+.09*math.sin(y*math.pi/2),.985,1))
im.pixels.foreach_set(px);im.colorspace_settings.name='Non-Color';im.pack()
for n in ['navy','teal','orange','purple','white']:
    nt=M[n].node_tree;t=nt.nodes.new('ShaderNodeTexImage');t.image=im;t.extension='REPEAT'
    uv=nt.nodes.new('ShaderNodeTexCoord');mapping=nt.nodes.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=3
    normal=nt.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.28
    nt.links.new(uv.outputs['UV'],mapping.inputs[0]);nt.links.new(mapping.outputs[0],t.inputs[0]);nt.links.new(t.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs[0],nt.nodes.get('Principled BSDF').inputs['Normal'])
for n in ['skin_kai','skin_zuri','pink']:
    p=M[n].node_tree.nodes.get('Principled BSDF');p.inputs['Subsurface Weight'].default_value=.055
COL=None; PARTS=[]
def bind(o,weights):
    for bone,value in weights.items():
        g=o.vertex_groups.get(bone) or o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),value,'REPLACE')
def register(o,n,mat,bone=None):
    o.name=n
    for c in list(o.users_collection):c.objects.unlink(o)
    COL.objects.link(o);o.data.materials.append(M[mat]);PARTS.append(o)
    for p in o.data.polygons:p.use_smooth=True
    if bone:bind(o,{bone:1})
    return o
def ell(n,p,s,mat,bone,segments=24,rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=p);o=bpy.context.object;o.scale=s
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return register(o,n,mat,bone)
def box(n,p,s,mat,bone,bevel=.01):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.scale=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    b=o.modifiers.new('Edge radius','BEVEL');b.width=bevel;b.segments=3;bpy.ops.object.modifier_apply(modifier=b.name)
    return register(o,n,mat,bone)
def surface(n,rings,mat,segments=24,sub=1):
    # Rings contain (center, radius_x, radius_y, skin weights).
    verts=[]; faces=[]
    for p,rx,ry,w in rings:
        for j in range(segments):
            a=j*math.tau/segments;verts.append((p[0]+rx*math.cos(a),p[1]+ry*math.sin(a),p[2]))
    for i in range(len(rings)-1):
        for j in range(segments):faces.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
    faces.extend([tuple(range(segments-1,-1,-1)),tuple((len(rings)-1)*segments+j for j in range(segments))])
    d=bpy.data.meshes.new(n);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(n,d);COL.objects.link(o);d.materials.append(M[mat]);PARTS.append(o)
    uv=d.uv_layers.new(name='UVMap')
    for poly in d.polygons:
        for li in poly.loop_indices:
            vi=d.loops[li].vertex_index;uv.data[li].uv=(vi%segments/segments,vi//segments/max(1,len(rings)-1))
        poly.use_smooth=True
    for i,(_,_,_,weights) in enumerate(rings):
        for bone,value in weights.items():
            g=o.vertex_groups.get(bone) or o.vertex_groups.new(name=bone);g.add(list(range(i*segments,(i+1)*segments)),value,'REPLACE')
    if sub:
        bpy.context.view_layer.objects.active=o;o.select_set(True);m=o.modifiers.new('Anatomical surface','SUBSURF');m.levels=sub;bpy.ops.object.modifier_apply(modifier=m.name);o.select_set(False)
    return o
def tube(n,points,radii,mat,bone,segments=10):
    vs=[];faces=[]
    for i,p in enumerate(points):
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        tangent.normalize();x=tangent.cross(Vector((0,1,0)))
        if x.length<.01:x=tangent.cross(Vector((1,0,0)))
        x.normalize();y=tangent.cross(x).normalized()
        for j in range(segments):
            a=math.tau*j/segments;v=Vector(p)+radii[i]*(math.cos(a)*x+math.sin(a)*y);vs.append(v)
    for i in range(len(points)-1):
        for j in range(segments):faces.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
    faces.extend([tuple(range(segments-1,-1,-1)),tuple((len(points)-1)*segments+j for j in range(segments))])
    d=bpy.data.meshes.new(n);d.from_pydata(vs,[],faces);d.update();o=bpy.data.objects.new(n,d);COL.objects.link(o);d.materials.append(M[mat]);PARTS.append(o);bind(o,{bone:1})
    for f in d.polygons:f.use_smooth=True
    return o
def face_human(name,skin):
    surface('Facial anatomy',[( (0,.008,z),rx,ry,{'head':1}) for z,rx,ry in [(1.625,.042,.052),(1.65,.068,.067),(1.685,.080,.073),(1.72,.092,.086),(1.765,.108,.102),(1.81,.110,.099),(1.86,.105,.096),(1.90,.091,.085),(1.935,.056,.057),(1.947,.014,.022)]],skin,32,2)
    for side in [-1,1]:
        x=side*.044
        ell('Inset sclera',(x,-.087,1.799),(.024,.010,.010),'eye','head')
        ell('Iris',(x,-.101,1.799),(.010,.003,.0095),'iris','head',20,12)
        ell('Pupil',(x,-.104,1.799),(.004,.0015,.005),'black','head',16,8)
        for upper in [True,False]:
            pts=[]
            for i in range(9):
                u=i/8;pts.append((x-.025+u*.05,-.090-.010*math.sin(math.pi*u),1.799+(1 if upper else -1)*.0105*math.sin(math.pi*u)))
            tube('Upper eyelid' if upper else 'Lower eyelid',pts,[.003]*9,skin,'head',8)
        tube('Eyebrow',[(x-.029,-.087,1.827),(x,-.099,1.835),(x+.03,-.087,1.828)],[.004,.005,.0025],'hair','head')
        ell('Ear helix',(side*.108,.005,1.77),(.017,.024,.044),skin,'head')
        ell('Ear inner',(side*.119,-.011,1.773),(.006,.012,.023),'lip_'+name.lower(),'head',16,10)
        # Cheek volume is part of the main facial surface.
    # Bridge, cartilage, alae and subtle nostrils; deliberately small human features.
    ell('Nasal bridge',(0,-.098,1.777),(.014,.020,.039),skin,'head')
    ell('Nose tip',(0,-.126,1.747),(.020,.017,.014),skin,'head')
    for side in [-1,1]:
        ell('Nostril wing',(side*.016,-.112,1.741),(.011,.013,.008),skin,'head',20,12)
        ell('Nostril',(side*.012,-.123,1.736),(.005,.003,.0025),'lip_'+name.lower(),'head',16,8)
    lip='lip_'+name.lower()
    tube('Upper lip',[(-.028,-.078,1.706),(-.012,-.086,1.709),(0,-.088,1.706),(.012,-.086,1.709),(.028,-.078,1.706)],[.002,.004,.003,.004,.002],lip,'head')
    tube('Lower lip',[(-.027,-.079,1.702),(0,-.088,1.699),(.027,-.079,1.702)],[.002,.004,.002],lip,'head')
    # Hair follows scalp; separate strand ridges catch light.
    ell('Hair mass',(0,.022,1.900),(.102,.094,.061),'hair','head',32,20)
    for i in range(11):
        x=-.083+i*.0166
        tube('Hair swept strand',[(x,-.049,1.917),(x*.94,.01,1.962),(x*.75,.071,1.922)],[.0035,.005,.003],'hair','head',8)
    if name=='Zuri':
        ell('Hair bun',(0,.13,1.886),(.069,.061,.073),'hair','head')
        for i in range(10):
            a=math.tau*i/10;tube('Bun braid',[(math.cos(a)*.05,.12,1.886+math.sin(a)*.058),(math.cos(a)*.054,.16,1.886+math.sin(a)*.06),(math.cos(a)*.038,.182,1.886+math.sin(a)*.043)],[.008]*3,'hair','head',8)
    else:
        tube('Teal hair band',[(-.095,-.012,1.908),(-.073,-.067,1.921),(0,-.079,1.927),(.073,-.067,1.921),(.095,-.012,1.908)],[.011]*5,'teal','head')

def animal_head(kind,skin):
    if kind=='shark':
        ell('Shark cranium',(0,.012,1.81),(.17,.15,.21),skin,'head',32,20)
        ell('Shark rostrum',(0,-.13,1.76),(.15,.145,.079),skin,'head',32,20)
        ell('Countershaded jaw',(0,-.104,1.696),(.135,.124,.038),'white','head')
        for side in [-1,1]:
            eye=(side*.126,-.090,1.82);ell('Shark eye',eye,(.027,.024,.021),'black','head')
            for i in range(3):tube('Gill slit',[(side*.142,.026+i*.021,1.79),(side*.159,.023+i*.021,1.73)],[.004,.003],'navy','head')
        tube('Mouth line',[(-.12,-.166,1.706),(0,-.227,1.697),(.12,-.166,1.706)],[.003]*3,'navy','head')
        for i in range(7):
            x=(i-3)*.021;tube('Small tooth',[(x,-.219,1.699),(x,-.221,1.686)],[.006,.001],'white','head',6)
        # Dorsal fin and flattened caudal tail retain a readable species silhouette.
        tube('Dorsal support',[(0,.1,1.47),(0,.28,1.42),(0,.37,1.28)],[.085,.065,.002],skin,'chest',12)
    elif kind in ['otter','capy']:
        cap=kind=='capy';ell('Animal skull',(0,.01,1.79),(.129 if cap else .108,.117,.156),skin,'head',32,20)
        ell('Muzzle',(0,-.11,1.716),(.112 if cap else .070,.098 if cap else .060,.066 if cap else .040),'muzzle','head')
        ell('Nose',(0,-(.203 if cap else .164),1.735),(.034,.018,.019),'rubber','head')
        for side in [-1,1]:
            ell('Ear',(side*.095,.005,1.918),(.037,.02,.043),skin,'head')
            ell('Ear inset',(side*.095,-.016,1.918),(.023,.005,.028),'brown','head')
            ell('Animal eye',(side*.069,-.083,1.813),(.019,.013,.017),'black','head')
            for i in range(3):tube('Whisker',[(side*.049,-.154,1.728-i*.008),(side*(.11+i*.018),-.165,1.735-i*.013)],[.0012,.0004],'white','head',6)
        if not cap:
            tube('Otter tail',[(0,.10,.95),(0,.25,.78),(0,.37,.48),(0,.44,.34)],[.064,.067,.042,.008],skin,'pelvis',16)
    elif kind=='axolotl':
        ell('Axolotl skull',(0,0,1.80),(.13,.107,.153),skin,'head',32,20)
        ell('Axolotl muzzle',(0,-.082,1.727),(.098,.054,.034),skin,'head')
        for side in [-1,1]:
            ell('Animal eye',(side*.070,-.088,1.819),(.019,.015,.020),'black','head')
            for j in range(3):
                root=(side*.107,.017,1.75+j*.063);tip=(side*(.21+(.02 if j==1 else 0)),.009,1.76+j*.097)
                tube('Gill stalk',[root,tip],[.012,.004],'pink','head')
                for k in range(5):
                    t=(k+1)/6;p=Vector(root).lerp(Vector(tip),t)
                    for sign in [-1,1]:tube('Gill filament',[p,p+Vector((side*.015,sign*.023,.023))],[.004,.001],'pink','head',6)
        tube('Mouth',[(-.065,-.111,1.717),(0,-.132,1.710),(.065,-.111,1.717)],[.002]*3,'purple','head')
    elif kind=='robot':
        box('Robot cranial shell',(0,0,1.80),(.24,.20,.285),'metal','head',.044)
        box('Recessed faceplate',(0,-.107,1.805),(.196,.03,.164),'glass','head',.025)
        for side in [-1,1]:
            ell('Optical lens',(side*.053,-.128,1.825),(.023,.013,.023),'teal','head')
            ell('Lens center',(side*.053,-.139,1.825),(.01,.004,.01),'white','head')
            box('Ear actuator',(side*.137,0,1.795),(.035,.095,.09),'rubber','head',.012)
            for z in [1.76,1.78]:box('Vent slot',(side*.059,-.127,z),(.06,.008,.004),'metal','head',.001)
        tube('Antenna',[(.073,.03,1.942),(.073,.03,2.014)],[.004,.003],'metal','head')
        ell('Antenna diode',(.073,.03,2.02),(.01,.01,.012),'orange','head')
    else:
        ell('Octopus mantle',(0,.04,1.83),(.137,.13,.197),skin,'head',32,20)
        for side in [-1,1]:ell('Octopus eye',(side*.085,-.075,1.77),(.027,.025,.022),'yellow','head');ell('Horizontal pupil',(side*.085,-.098,1.77),(.018,.006,.005),'black','head')
        for i in range(4):
            a=(i-1.5)*.55
            pts=[(math.sin(a)*.08,.055,1.66),(math.sin(a)*.15,.13,1.56),(math.sin(a)*.20,.18,1.46),(math.sin(a)*.24,.14,1.43)]
            tube('Mantle arm',pts,[.025,.021,.014,.004],skin,'head',12)
            for p in pts[1:3]:ell('Sucker',Vector(p)+Vector((0,-.015,0)),(.012,.006,.012),'pink','head',12,8)

def fuse_human_face(skin):
    global PARTS
    heads=[o for o in PARTS if o.vertex_groups.get('head') and o.data.materials[0]==M[skin]]
    others=[o for o in PARTS if o not in heads]
    bpy.ops.object.select_all(action='DESELECT')
    for o in heads:o.select_set(True)
    bpy.context.view_layer.objects.active=heads[0];bpy.ops.object.join();o=bpy.context.object;o.name='Unified facial skin'
    rem=o.modifiers.new('Fuse facial anatomy','REMESH');rem.mode='VOXEL';rem.voxel_size=.0024;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
    smooth=o.modifiers.new('Relax skin transitions','SMOOTH');smooth.factor=.85;smooth.iterations=5;bpy.ops.object.modifier_apply(modifier=smooth.name)
    o.vertex_groups.clear();bind(o,{'head':1});PARTS=others+[o]
    for obj in PARTS:
        if obj.vertex_groups.get('head'):obj.location.z-=.035

def make_rider(name,kind,skin,accent,width=1,height=1):
    global COL,PARTS
    COL=bpy.data.collections.new(name);scene.collection.children.link(COL);PARTS=[]
    # Athletic torso with pelvis, waist, ribs and shoulder contours.
    surface('Wetsuit torso',[( (0,0,z),rx,ry,w) for z,rx,ry,w in [(.91,.125,.080,{'pelvis':1}),(.96,.159,.098,{'pelvis':1}),(1.04,.157,.096,{'pelvis':.7,'spine':.3}),(1.12,.127,.077,{'spine':1}),(1.21,.143,.087,{'spine':.65,'chest':.35}),(1.33,.179,.105,{'chest':1}),(1.43,.200,.100,{'chest':1}),(1.49,.180,.080,{'chest':1}),(1.525,.103,.066,{'chest':.5,'neck':.5}),(1.54,.06,.058,{'neck':1})]],'navy',32,2)
    surface('Neck',[( (0,0,z),rx,ry,{'neck':1}) for z,rx,ry in [(1.49,.053,.051),(1.54,.050,.050),(1.59,.049,.049),(1.625 if kind=='human' else 1.71,.06,.059)]],skin,24,1)
    # Fitted segmented flotation vest; space for shoulder articulation.
    for side in [-1,1]:
        panel=box('Shaped flotation panel',(side*.086,-.096,1.338),(.137,.055,.265),accent,'chest',.022)
        panel.rotation_euler.y=side*-.065
        tube('Vest piping',[(side*.028,-.109,1.19),(side*.023,-.135,1.33),(side*.030,-.102,1.47)],[.004]*3,'white','chest')
        box('Reflective chest tape',(side*.092,-.132,1.414),(.048,.008,.014),'white','chest',.002)
        for z in [1.22,1.31]:box('Compression strap',(side*.15,-.061,z),(.08,.03,.024),'navy','chest',.004)
    box('Vest zipper',(0,-.127,1.328),(.009,.01,.267),'metal','chest',.002)
    for i in range(16):box('Zipper tooth',((-.004 if i%2 else .004),-.134,1.205+i*.015),(.007,.006,.004),'metal','chest',.001)
    box('Zipper pull',(0,-.14,1.44),(.017,.007,.025),'metal','chest',.003)
    surface('Waist belt',[((0,0,z),.144,.091,{'spine':.3,'pelvis':.7}) for z in [1.053,1.058,1.079,1.084]],'rubber',32,1)
    box('Belt buckle',(0,-.10,1.067),(.055,.016,.039),'metal','pelvis',.005)
    for side in [-1,1]:
        sn='L' if side<0 else 'R';thigh='thigh.'+sn;shin='shin.'+sn;foot='foot.'+sn;upper='upper_arm.'+sn;fore='forearm.'+sn;hand='hand.'+sn
        x=side*.105
        # Continuous quad strips cross the knee and elbow, with blended weights.
        leg=[]
        for z,rx,ry,cy,w in [(.12,.039,.043,.017,{shin:1}),(.20,.043,.049,.020,{shin:1}),(.33,.063,.066,.024,{shin:1}),(.43,.066,.064,.005,{shin:1}),(.50,.053,.057,-.010,{shin:.85,thigh:.15}),(.54,.052,.058,-.022,{shin:.5,thigh:.5}),(.58,.058,.064,-.019,{shin:.15,thigh:.85}),(.66,.077,.081,-.001,{thigh:1}),(.79,.089,.096,.005,{thigh:1}),(.91,.092,.094,.0,{thigh:.8,'pelvis':.2}),(.99,.077,.072,0,{thigh:.3,'pelvis':.7})]:leg.append(((x,cy,z),rx,ry,w))
        surface('Leg anatomy '+sn,leg,'navy',24,2)
        # Fitted knee panel makes the actual joint visible without ball joints.
        o=ell('Patella reinforcement '+sn,(x,-.067,.548),(.043,.019,.049),'rubber',None)
        bind(o,{thigh:.5,shin:.5})
        tube('Thigh seam '+sn,[(x+side*.075,-.02,.91),(x+side*.077,-.022,.79),(x+side*.058,-.033,.64)],[.003]*3,accent,thigh)
        ell('Calf accent '+sn,(x+side*.039,-.023,.335),(.014,.044,.092),accent,shin)
        surface('Continuous boot '+sn,[((x,cy,z),rx,ry,{foot:1}) for z,cy,rx,ry in [(.024,-.067,.055,.119),(.034,-.067,.057,.121),(.065,-.060,.055,.116),(.089,-.038,.050,.094),(.118,.006,.044,.063),(.151,.017,.041,.045),(.170,.017,.040,.044)]],'navy',24,2)
        # Boot upper transitions continuously from toe to ankle.
        box('Sole '+sn,(x,-.067,.025),(.112,.243,.028),'rubber',foot,.015)
        for i in range(4):tube('Boot lace '+sn,[(x-.027,-.111+i*.022,.091),(x+.027,-.100+i*.022,.091)],[.0025,.0025],'white',foot,8)
        for i in range(5):box('Sole tread '+sn,(x,-.151+i*.036,.013),(.10,.012,.010),'rubber',foot,.002)
        arm=[]
        for px,py,z,rx,ry,w in [(.385,-.031,1.024,.030,.030,{fore:1}),(.38,-.027,1.065,.036,.034,{fore:1}),(.352,-.021,1.145,.045,.043,{fore:1}),(.322,-.012,1.213,.039,.038,{fore:.75,upper:.25}),(.313,-.007,1.24,.037,.038,{fore:.5,upper:.5}),(.303,-.003,1.267,.041,.041,{fore:.2,upper:.8}),(.277,0,1.34,.059,.055,{upper:1}),(.241,.0,1.419,.068,.061,{upper:.9,'chest':.1}),(.205,0,1.467,.066,.063,{upper:.6,'chest':.4}),(.177,0,1.473,.044,.045,{'chest':1})]:arm.append(((side*px,py,z),rx,ry,w))
        surface('Arm anatomy '+sn,arm,skin,24,2)
        # Neoprene sleeve near the shoulder; underlying continuous mesh remains skinned.
        surface('Short sleeve '+sn,[((side*.278,0,1.337),.064,.061,{upper:1}),((side*.263,0,1.377),.067,.063,{upper:1}),((side*.242,0,1.424),.072,.065,{upper:1}),((side*.215,0,1.465),.074,.070,{upper:.75,'chest':.25}),((side*.19,0,1.480),.052,.052,{'chest':.8,upper:.2})],accent,24,1)
        # Subtle elbow ridge on the back; joint is part of continuous limb mesh.
        elbow=ell('Elbow contour '+sn,(side*.314,.022,1.242),(.025,.016,.034),skin,None);bind(elbow,{upper:.5,fore:.5})
        surface('Wrist cuff '+sn,[((side*.385,-.031,z),.034,.033,{fore:1}) for z in [1.024,1.028,1.05,1.055]],'navy',24,1)
        # Four individually modeled fingers and one thumb. ALL weighted to hand.
        palm=(side*.395,-.034,.976)
        ell('Hand palm '+sn,palm,(.041,.021,.061),skin,hand,24,16)
        for j,length in enumerate([.065,.077,.073,.056]):
            fx=side*(.365+j*.019);z=.941+(0.007 if j in [0,3] else 0)
            points=[(fx,-.036,z),(fx+side*.003,-.04,z-length*.4),(fx+side*.006,-.052,z-length*.78),(fx+side*.004,-.064,z-length)]
            tube('Static finger %s %s'%(j+1,sn),points,[.009,.009,.0075,.005],skin,hand,12)
            ell('Knuckle %s %s'%(j+1,sn),points[1],(.0095,.009,.011),skin,hand,16,10)
            ell('Fingernail %s %s'%(j+1,sn),(points[-1][0],points[-1][1]-.004,points[-1][2]+.009),(.0046,.002,.006),'muzzle' if kind!='human' else skin,hand,12,8)
        tube('Static thumb '+sn,[(side*.363,-.035,.996),(side*.343,-.057,.974),(side*.34,-.075,.951)],[.014,.011,.007],skin,hand,12)
    if kind=='human':
        face_human(name,skin);fuse_human_face(skin)
    else:animal_head(kind,skin)
    # Join into one skinned mesh. Static fingers retain hand weights, never digit bones.
    bpy.ops.object.select_all(action='DESELECT')
    for o in PARTS:o.select_set(True)
    bpy.context.view_layer.objects.active=PARTS[0];bpy.ops.object.join();body=bpy.context.object;body.name=name+'_SkinnedMesh'
    # Bake proportion changes into geometry and apply the same transformation to bones.
    for v in body.data.vertices:v.co.x*=width;v.co.z*=height
    def P(v):return (v[0]*width,v[1],v[2]*height)
    arm=bpy.data.armatures.new(name+'_Skeleton');rig=bpy.data.objects.new(name+'_Rig',arm);COL.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);body.select_set(False)
    bpy.ops.object.mode_set(mode='EDIT')
    def bone(n,h,t,parent=None,deform=True):
        b=arm.edit_bones.new(n);b.head=P(h);b.tail=P(t);b.use_deform=deform
        if parent:b.parent=arm.edit_bones[parent]
        return b
    bone('root',(0,0,0),(0,0,.2),deform=False);bone('pelvis',(0,0,.94),(0,0,1.08),'root');bone('spine',(0,0,1.08),(0,0,1.28),'pelvis');bone('chest',(0,0,1.28),(0,0,1.50),'spine');bone('neck',(0,0,1.50),(0,0,1.64),'chest');bone('head',(0,0,1.64),(0,0,1.94),'neck')
    for side in [-1,1]:
        sn='L' if side<0 else 'R'
        bone('clavicle.'+sn,(side*.025,0,1.48),(side*.205,0,1.467),'chest')
        bone('upper_arm.'+sn,(side*.205,0,1.467),(side*.313,-.007,1.24),'clavicle.'+sn)
        bone('forearm.'+sn,(side*.313,-.007,1.24),(side*.385,-.031,1.034),'upper_arm.'+sn)
        bone('hand.'+sn,(side*.385,-.031,1.034),(side*.395,-.034,.95),'forearm.'+sn)
        bone('thigh.'+sn,(side*.105,0,.94),(side*.105,-.022,.54),'pelvis')
        bone('shin.'+sn,(side*.105,-.022,.54),(side*.105,.017,.13),'thigh.'+sn)
        bone('foot.'+sn,(side*.105,.017,.13),(side*.105,-.16,.04),'shin.'+sn)
        bone('CTRL_hand.'+sn,(side*.385,-.031,1.034),(side*.385,-.031,1.12),'root',False)
        bone('CTRL_elbow.'+sn,(side*.40,-.42,1.24),(side*.40,-.42,1.30),'root',False)
        bone('CTRL_foot.'+sn,(side*.105,.017,.13),(side*.105,-.15,.13),'root',False)
        bone('CTRL_knee.'+sn,(side*.105,-.45,.54),(side*.105,-.45,.60),'root',False)
    bpy.ops.object.mode_set(mode='OBJECT')
    body.parent=rig;mod=body.modifiers.new('Deforming body rig','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
    rig.show_in_front=True;arm.display_type='OCTAHEDRAL'
    rig['instructions']='FK pose bones drive the skin. Optional hand/foot IK constraints default to zero influence; enable when using controls. Fingers/thumbs have no bones and are fully weighted to each hand.'
    # Explicit elbow/knee bending is included in the motion test.
    for f,bend,lean in [(1,0,0),(20,0,0),(40,.7,0),(60,1.1,-.15),(80,.7,.15),(100,0,0)]:
        for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0)
        rig.pose.bones['chest'].rotation_euler.y=lean
        for sn in ['L','R']:
            rig.pose.bones['forearm.'+sn].rotation_euler.x=-bend
            rig.pose.bones['thigh.'+sn].rotation_euler.x=-bend*.4
            rig.pose.bones['shin.'+sn].rotation_euler.x=bend*.8
        for pb in rig.pose.bones:
            if pb.bone.use_deform:pb.keyframe_insert('rotation_euler',frame=f)
    rig.animation_data.action.name=name+'_Joint_Bend_Test';scene.frame_start=1;scene.frame_end=100;scene.frame_set(1)
    body['static_fingers']=True;body['finger_bones']=0
    # Show one rider at a time while exporting to avoid sampling unrelated rigs.
    for lc in scene.view_layers[0].layer_collection.children:lc.exclude=lc.name!=name
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=rig
    body.data.calc_loop_triangles();triangles=len(body.data.loop_triangles)
    for level,ratio in ([] if '--lookdev' in sys.argv else [(0,1),(1,.55),(2,.25)]):
        dec=None
        if level:dec=body.modifiers.new('Runtime LOD','DECIMATE');dec.ratio=ratio
        suffix='' if not level else '_LOD'+str(level)
        bpy.ops.export_scene.gltf(filepath=str(R/'exports'/f'{name}{suffix}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_skins=True,export_def_bones=True,export_animation_mode='ACTIVE_ACTIONS',export_force_sampling=False,export_animations=(level==0),export_frame_step=4,export_extras=True)
        if dec:body.modifiers.remove(dec)
    for side in ['L','R']:
        for limb,pole,target in [('forearm','elbow','hand'),('shin','knee','foot')]:
            con=rig.pose.bones[limb+'.'+side].constraints.new('IK');con.name='Optional IK — enable influence to pose';con.target=rig;con.subtarget='CTRL_'+target+'.'+side;con.pole_target=rig;con.pole_subtarget='CTRL_'+pole+'.'+side;con.chain_count=2;con.influence=0
    return {'name':name,'category':'character','triangles_lod0':triangles,'bones':len(arm.bones),'finger_bones':0,'skinned':True,'notes':'Revision 2: continuous elbow/knee topology, skinned body, fixed five-digit hands, FK and optional IK controls, joint-bend test.'}

inventory=[]
roster=[('Kai','human','skin_kai','orange',1,1),('Zuri','human','skin_zuri','orange',.91,.98),('Riptide','shark','blue','teal',1.26,1.08),('Pip','otter','brown','teal',.85,.86),('Marina','axolotl','pink','teal',.94,1.02),('Bolt','robot','metal','teal',1,1.04),('Mochi','capy','tan','orange',1.22,.96),('Ink','octopus','purple','teal',1.02,1.01)]
if '--sample' in sys.argv or '--lookdev' in sys.argv:roster=roster[:2]
for args in roster:
    for lc in scene.view_layers[0].layer_collection.children:lc.exclude=False
    inventory.append(make_rider(*args));print('RIDER_COMPLETE',args[0],flush=True)
for lc in scene.view_layers[0].layer_collection.children:lc.exclude=True
stage=bpy.data.collections.new('Presentation_V2');scene.collection.children.link(stage)
def link(o):
    for c in list(o.users_collection):c.objects.unlink(o)
    stage.objects.link(o)
def text_label(body,p,size):
    d=bpy.data.curves.new('Label','FONT');d.body=body;d.align_x='CENTER';d.size=size;d.extrude=.001;o=bpy.data.objects.new(body,d);stage.objects.link(o);o.location=p;o.rotation_euler=(math.pi/2,0,0);d.materials.append(M['white'])
def arrange(names):
    for o in list(stage.objects):
        if o.instance_type=='COLLECTION' or o.type=='FONT':bpy.data.objects.remove(o,do_unlink=True)
    for i,name in enumerate(names):
        o=bpy.data.objects.new(name+'_display',None);stage.objects.link(o);o.instance_type='COLLECTION';o.instance_collection=bpy.data.collections[name];o.location=((i-(len(names)-1)/2)*.95,0,0)
        text_label(name,(o.location.x,-.17,-.075),.09)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.02));floor=bpy.context.object;link(floor);floor.data.materials.append(M['navy'])
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for n,loc,power,size in [('Key',(-3,-5,6),1000,5),('Fill',(4,-3,4),850,4),('Rim',(0,3,5),1300,4)]:
    d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);stage.objects.link(o);o.location=loc;aim(o,(0,0,1))
d=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',d);stage.objects.link(cam);scene.camera=cam;d.type='ORTHO'
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
def render(file,names,loc,scale,res):
    arrange(names);cam.location=loc;aim(cam,(0,0,1));d.ortho_scale=scale;scene.render.resolution_x=res[0];scene.render.resolution_y=res[1];scene.render.filepath=str(R/'previews'/file);bpy.ops.render.render(write_still=True)
render('11_anatomy_revision.png',[x[0] for x in roster[:2]],(2,-7,2.8),2.7,(1400,1400))
if len(roster)>2:render('01_characters.png',[x[0] for x in roster],(.7,-10,3.1),8.2,(2200,1050))
scene.frame_set(60)
render('12_joint_bend_test.png',['Kai'],(2,-6,2.8),2.55,(1100,1200));scene.frame_set(1)
arrange(['Kai']);cam.location=(.78,-1.3,1.12);aim(cam,(.395,-.04,.95));d.ortho_scale=.31;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.filepath=str(R/'previews/13_hand_detail.png');bpy.ops.render.render(write_still=True)
arrange([x[0] for x in roster]);cam.location=(.7,-10,3.1);aim(cam,(0,0,1));d.ortho_scale=8.2 if len(roster)>2 else 2.7
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/Hydro_Drift_Characters.blend'),compress=True)
(R/'characters_v2.json').write_text(json.dumps(inventory,indent=2))
print('CHARACTERS_V2_COMPLETE',flush=True)



