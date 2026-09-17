"""Rebuild original Hydro Drift riders with connected anatomical control cages.
Run Blender --background --python assets/rebuild_riders_v3.py -- --hero for look development.
"""
import bpy, math, sys, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from surface_modeling import *
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Characters.blend'))
scene=bpy.context.scene;scene.frame_set(1)
ROSTER=[('Kai','human','skin_kai','orange',1,1),('Zuri','human','skin_zuri','orange',.91,.98),('Riptide','shark','blue','teal',1.26,1.08),('Pip','otter','brown','teal',.85,.86),('Marina','axolotl','pink','teal',.94,1.02),('Bolt','robot','metal','teal',1,1.04),('Mochi','capy','tan','orange',1.22,.96),('Ink','octopus','purple','teal',1.02,1.01)]
rigs={name:bpy.data.objects[name+'_Rig'] for name,*_ in ROSTER}
for obj in list(bpy.data.objects):
    if obj not in rigs.values():bpy.data.objects.remove(obj,do_unlink=True)
for col in list(bpy.data.collections):
    if col.name not in rigs:bpy.data.collections.remove(col)
for lc in scene.view_layers[0].layer_collection.children:lc.exclude=False;lc.hide_viewport=False
M={m.name:m for m in bpy.data.materials}
def mat(name,c,rough=.45,metal=0):
    m=bpy.data.materials.new('V3_'+name);m.use_nodes=True;m.diffuse_color=(*c,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m
M['suit']=mat('Technical_neoprene',(.018,.026,.038),.58)
M['seam']=mat('Raised_woven_seams',(.09,.12,.14),.67)
M['eye_v3']=mat('Eye_sclera',(.56,.60,.53),.29)
M['lens']=mat('Iris',(.028,.065,.054),.25)
M['hair_v3']=mat('Sculpted_hair',(.008,.005,.003),.82)
M['hair_v3'].node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.22
M['lip_v3']=mat('Lips',(.28,.085,.058),.43)
M['sole_v3']=mat('Molded_boot_sole',(.012,.015,.018),.73)
M['muzzle_v3']=mat('Warm_muzzle',(.50,.34,.20),.75)
M['shark_v3']=mat('Shark_countershade',(.43,.62,.65),.53)
M['nose_v3']=mat('Animal_nose',(.018,.012,.009),.45)
# Shared packed textile normals export to GLB and work in the game renderer.
image=bpy.data.images.get('Woven_neoprene_normal_256')
if image:
    nt=M['suit'].node_tree;t=nt.nodes.new('ShaderNodeTexImage');t.image=image
    coord=nt.nodes.new('ShaderNodeTexCoord');scale=nt.nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=6
    normal=nt.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.18
    nt.links.new(coord.outputs['UV'],scale.inputs[0]);nt.links.new(scale.outputs[0],t.inputs[0]);nt.links.new(t.outputs[0],normal.inputs[1]);nt.links.new(normal.outputs[0],nt.nodes.get('Principled BSDF').inputs['Normal'])

def torso_weights(z):
    if z<1.06:return {'pelvis':1}
    if z<1.18:t=clamp((z-1.06)/.12);return {'pelvis':1-t,'spine':t}
    if z<1.32:t=clamp((z-1.18)/.14);return {'spine':1-t,'chest':t}
    if z<1.51:return {'chest':1}
    if z<1.60:t=clamp((z-1.51)/.09);return {'chest':1-t,'neck':t}
    t=clamp((z-1.60)/.04);return {'neck':1-t,'head':t}

def leg_weights(z,sn):
    if z>.89:t=clamp((z-.89)/.11);return {'thigh.'+sn:1-t,'pelvis':t}
    if z>.595:return {'thigh.'+sn:1}
    if z>.495:t=clamp((z-.495)/.10);return {'shin.'+sn:1-t,'thigh.'+sn:t}
    if z>.17:return {'shin.'+sn:1}
    t=clamp((z-.08)/.09);return {'foot.'+sn:1-t,'shin.'+sn:t}

def arm_weights(z,sn):
    if z>1.44:t=clamp((z-1.44)/.06);return {'upper_arm.'+sn:1-t,'clavicle.'+sn:t}
    if z>1.29:return {'upper_arm.'+sn:1}
    if z>1.19:t=clamp((z-1.19)/.10);return {'forearm.'+sn:1-t,'upper_arm.'+sn:t}
    if z>1.06:return {'forearm.'+sn:1}
    t=clamp((z-1.015)/.045);return {'hand.'+sn:1-t,'forearm.'+sn:t}

HEAD_X=[(1.60,.049),(1.64,.054),(1.665,.068),(1.695,.079),(1.735,.088),(1.775,.105),(1.815,.106),(1.85,.105),(1.895,.10),(1.93,.083),(1.955,.054),(1.972,.008)]
HEAD_Y=[(1.60,.052),(1.64,.05),(1.665,.055),(1.695,.067),(1.735,.081),(1.775,.093),(1.815,.10),(1.85,.10),(1.895,.097),(1.93,.085),(1.955,.056),(1.972,.01)]
def face_offset(x,z,kind):
    nose=-.018*gauss(x,0,.014)*gauss(z,1.783,.044)-.027*gauss(x,0,.020)*gauss(z,1.751,.013)
    nose-=.009*(gauss(x,-.019,.009)+gauss(x,.019,.009))*gauss(z,1.744,.009)
    cheeks=-.008*(gauss(x,-.063,.025)+gauss(x,.063,.025))*gauss(z,1.769,.023)
    sockets=.012*(gauss(x,-.043,.025)+gauss(x,.043,.025))*gauss(z,1.804,.014)
    brow=-.009*(gauss(x,-.043,.028)+gauss(x,.043,.028))*gauss(z,1.827,.009)
    mouth=-.006*gauss(x,0,.028)*gauss(z,1.711,.0038)-.007*gauss(x,0,.025)*gauss(z,1.701,.004)
    mouth+=.003*gauss(x,0,.032)*gauss(z,1.706,.0018)
    chin=-.008*gauss(x,0,.032)*gauss(z,1.671,.014)
    if kind=='human':return nose+cheeks+sockets+brow+mouth+chin
    if kind in ['otter','capy']:
        return -.065*gauss(x,0,.09 if kind=='capy' else .071)*gauss(z,1.731,.038)+sockets*.75
    if kind=='shark':return -.09*gauss(x,0,.14)*gauss(z,1.755,.052)+sockets
    if kind=='axolotl':return -.018*gauss(x,0,.10)*gauss(z,1.731,.035)+sockets*.5
    if kind=='octopus':return -.025*gauss(x,0,.085)*gauss(z,1.752,.023)+sockets*.4
    return -.012*gauss(x,0,.085)*gauss(z,1.80,.085)

def skull_radii(z,kind):
    rx=profile(HEAD_X,z);ry=profile(HEAD_Y,z)
    if kind!='human':rx*=1.2
    if kind=='shark':rx*=1.1+.35*gauss(z,1.74,.06);ry*=1.14
    if kind=='otter':rx*=1+.18*gauss(z,1.73,.055)
    if kind=='capy':rx*=1+.30*gauss(z,1.73,.065);ry*=1+.22*gauss(z,1.74,.06)
    if kind=='octopus':rx*=1+.12*gauss(z,1.89,.07);ry*=1.18
    if kind=='robot':rx*=1.06
    return rx,ry

def face_y(x,z,kind):
    rx,ry=skull_radii(z,kind)
    cosine=min(.999,abs(x)/max(.001,rx))
    if kind=='robot':cosine=cosine**(1/.58)
    sine=math.sqrt(max(.001,1-cosine*cosine))
    return .008-ry*(sine**.60 if kind=='robot' else sine)+face_offset(x,z,kind)*sine**6

def connected_body(name,kind,skin,accent,col):
    s=Surface(name+'_ConnectedBody');mats=[M['suit'],M[skin],M[accent],M['sole_v3'],M['seam'],M['muzzle_v3'],M['shark_v3']]
    shape=[(.94,.16,.096),(.975,.168,.105),(1.02,.161,.104),(1.075,.145,.094),(1.13,.132,.087),(1.20,.144,.093),(1.27,.168,.104),(1.33,.184,.111),(1.39,.195,.113),(1.44,.195,.10),(1.48,.173,.083),(1.50,.132,.064),(1.535,.066,.052),(1.575,.049,.05),(1.61,.05,.053)]
    rows=[];faces={};n=48
    for z,rx,ry in shape:
        pts=[]
        for j in range(n):
            a=TAU*j/n;ripple=.0015*math.sin(a*5+z*165)*(gauss(z,1.075,.035)+gauss(z,1.2,.035))
            x=(rx+ripple)*math.cos(a);y=(ry+ripple)*math.sin(a)
            if y<0:y-=.005*gauss(abs(x),.088,.045)*gauss(z,1.36,.07)
            pts.append((x,y,z))
        rows.append(s.ring(pts,torso_weights(z)))
    for i in range(len(rows)-1):
        for j in range(n):faces[i,j]=s.face((rows[i][j],rows[i][(j+1)%n],rows[i+1][(j+1)%n],rows[i+1][j]),1 if i>=12 else 0)
    # A saddle of shared crotch edges bifurcates the hip ring into two thigh rings.
    # This avoids a flat pelvis cap with small holes and visibly pinched leg roots.
    saddle=[rows[0][12]]+[s.vertex((0,lerp(.096,-.096,i/8),.94-.052*math.sin(math.pi*i/8)),{'pelvis':1}) for i in range(1,8)]+[rows[0][36]]
    right=[rows[0][j%48] for j in range(36,61)]+saddle[1:-1]
    left=[rows[0][j] for j in range(12,37)]+list(reversed(saddle[1:-1]))
    for side,hole in [(-1,left),(1,right)]:
        sn='L' if side<0 else 'R';prev=hole
        specs=[(.91,.085,.085,0),(.86,.087,.09,.006),(.79,.082,.091,.01),(.71,.073,.085,.008),(.635,.061,.072,-.003),(.59,.054,.063,-.015),(.56,.055,.062,-.025),(.54,.055,.061,-.027),(.52,.052,.058,-.019),(.495,.051,.056,-.012),(.45,.061,.062,.004),(.39,.065,.069,.018),(.32,.057,.066,.027),(.25,.046,.056,.025),(.19,.036,.045,.021),(.145,.033,.039,.017),(.125,.035,.049,.004),(.095,.043,.081,-.025),(.072,.051,.112,-.06),(.047,.057,.121,-.064),(.028,.057,.12,-.066),(.018,.054,.117,-.066)]
        for z,rx,ry,cy in specs:
            pts=[]
            for j in range(24):
                a=TAU*j/24;wrinkle=.0015*math.sin(z*145+a*2)*gauss(z,.54,.075)
                patella=.009*max(0,-math.sin(a))**8*gauss(z,.55,.035)
                center_x=lerp(.105,.082,clamp((z-.70)/.22))
                rxx=rx*lerp(1,.89,clamp((z-.72)/.20))
                pts.append((side*center_x+(rxx+wrinkle)*math.cos(a),cy+(ry+wrinkle+patella)*math.sin(a),z))
            loop=s.ring(pts,leg_weights(z,sn));prev=s.bridge(prev,loop,3 if z<.048 else 0,align=True)
        s.cap(prev,3,{'foot.'+sn:1})
    for side in [-1,1]:
        sn='L' if side<0 else 'R';middle=0 if side>0 else n//2
        hole=s.cut([faces[i,(middle+j)%n] for i in range(8,11) for j in range(-3,3)])
        prev=hole
        specs=[(.218,1.448,.067,.064,0),(.244,1.419,.067,.062,0),(.269,1.371,.058,.055,0),(.29,1.319,.049,.048,-.003),(.303,1.275,.041,.040,-.004),(.311,1.251,.038,.039,-.007),(.317,1.230,.039,.039,-.010),(.326,1.202,.043,.040,-.014),(.343,1.166,.046,.041,-.019),(.361,1.117,.041,.036,-.025),(.378,1.069,.034,.030,-.029),(.385,1.034,.029,.027,-.031)]
        for index,(x,z,rx,ry,cy) in enumerate(specs):
            center=Vector((side*x,cy,z));direction=Vector([(side*1,0,-.10),(side*.85,0,-.4),(side*.55,0,-.83)][index] if index<3 else (side*.38,-.03,-.90)).normalized();u=Vector((0,1,0));v=direction.cross(u).normalized()
            pts=[]
            for j in range(24):
                a=TAU*j/24;fold=.0013*math.sin(a*2+z*160)*gauss(z,1.245,.036)
                pts.append(center+u*(ry+fold)*math.cos(a)+v*(rx+fold)*math.sin(a))
            loop=s.ring(pts,arm_weights(z,sn));prev=s.bridge(prev,loop,2 if z>1.34 else 1,align=True)
        # Palm, four fingers and thumb share boundary vertices with the wrist.
        palm_rows=[];palm_faces={};cx=side*.395
        for z,rx,ry,cy in [(1.016,.030,.024,-.033),(.997,.039,.025,-.034),(.978,.042,.022,-.036),(.955,.041,.020,-.039),(.937,.037,.018,-.041)]:
            row=s.ring([(cx+rx*math.cos(TAU*j/40),cy+ry*math.sin(TAU*j/40),z) for j in range(40)],{'hand.'+sn:1})
            if not palm_rows:row=s.bridge(prev,row,1,align=True)
            else:
                row=s.align(palm_rows[-1],row)
                for j in range(40):palm_faces[len(palm_rows)-1,j]=s.face((palm_rows[-1][j],palm_rows[-1][(j+1)%40],row[(j+1)%40],row[j]),1)
            palm_rows.append(row)
        outer,digits=s.grid_cap(cx,-.041,.937,.037,.018,16,4,[(i,i+2,1,3) for i in [1,5,9,13]],{'hand.'+sn:1},1)
        s.bridge(palm_rows[-1],outer,1,align=True)
        for j,hole in enumerate(digits):
            center=sum((Vector(s.v[i]) for i in hole),Vector())/len(hole)
            length=[.059,.077,.074,.056][j if side>0 else 3-j];points=[];radii=[]
            for k in range(11):
                t=k/10;points.append((center.x+side*.004*t,center.y-.022*t*t,.935-length*t))
                radii.append(.0075*(1-.40*t)+.0012*(gauss(t,.33,.10)+gauss(t,.68,.08)))
            radii[-1]=.0025;sweep(s,points,radii,1,{'hand.'+sn:1},12,hole,flat=.92)
        # Locate medial palm faces geometrically so both mirrored hands branch correctly.
        candidates=[]
        for (i,j),fi in palm_faces.items():
            if i not in [0,1]:continue
            c=sum((Vector(s.v[k]) for k in s.f[fi]),Vector())/4
            candidates.append(((c-Vector((cx-side*.036,-.041,.986))).length,fi))
        hole=s.cut([min(candidates)[1]])
        sweep(s,[(cx-side*.032,-.038,.991),(cx-side*.044,-.044,.982),(cx-side*.055,-.055,.970),(cx-side*.059,-.067,.953),(cx-side*.060,-.071,.943)],[.014,.014,.012,.009,.003],1,{'hand.'+sn:1},12,hole)
    # Craniofacial shape is displaced directly in this continuous neck/head surface.
    head_rows=[];head_faces={};prev=rows[-1]
    levels=sorted(set([1.625+i*.005 for i in range(70)]+[1.699,1.703,1.706,1.710,1.714,1.972]))
    levels=[z for z in levels if z<=1.972]
    for z in levels:
        rx,ry=skull_radii(z,kind)
        pts=[]
        for j in range(96):
            a=TAU*j/96;x=rx*math.cos(a);y=.008+ry*math.sin(a)
            if kind=='robot':
                x=rx*math.copysign(abs(math.cos(a))**.58,math.cos(a));y=.008+ry*math.copysign(abs(math.sin(a))**.60,math.sin(a))
            y+=face_offset(x,z,kind)*max(0,-math.sin(a))**6
            pts.append((x,y,z))
        row=s.ring(pts,torso_weights(z))
        if not head_rows:row=s.bridge(prev,row,1,align=True)
        else:
            for j in range(96):
                material=1
                if kind in ['otter','capy'] and 1.68<z<1.765 and 56<j<88:material=5
                if kind=='shark' and z<1.765 and 48<j<95:material=6
                head_faces[len(head_rows)-1,j]=s.face((head_rows[-1][j],head_rows[-1][(j+1)%96],row[(j+1)%96],row[j]),material)
        head_rows.append(row)
    s.cap(head_rows[-1],1,{'head':1})
    # Ears / gills emerge from actual holes in the skull, not intersecting objects.
    if kind in ['human','otter','capy','axolotl']:
        for side in [-1,1]:
            midpoint=0 if side>0 else 48
            for branch in (range(3) if kind=='axolotl' else range(1)):
                zbase=(1.755+branch*.055) if kind=='axolotl' else (1.884 if kind!='human' else 1.78)
                row=min(range(len(levels)-1),key=lambda i:abs(levels[i]-zbase))
                hole=s.cut([head_faces[row,(midpoint+j)%96] for j in [-1,0]])
                cx=side*skull_radii(zbase,kind)[0]
                if kind=='axolotl':
                    pts=[(cx,0,zbase),(cx+side*.04,.004,zbase+.015),(cx+side*.09,.0,zbase+.045),(cx+side*.12,-.003,zbase+.07)]
                    sweep(s,pts,[.014,.016,.012,.001],1,{'head':1},16,hole,flat=.40)
                else:
                    tall=.041 if kind=='human' else .039
                    prev=hole
                    for displacement,scale in [(0,1),(.006,1.04),(.012,.95),(.014,.74),(.008,.54),(.010,.15)]:
                        spread=displacement if kind=='human' else displacement*2.7
                        loop=s.ring([(cx+side*spread,.008+math.cos(TAU*j/32)*.021*scale,zbase+math.sin(TAU*j/32)*tall*scale) for j in range(32)],{'head':1})
                        prev=s.bridge(prev,loop,1,align=True)
                    s.cap(prev,1,{'head':1})
    if kind=='octopus':
        row=min(range(len(levels)-1),key=lambda i:abs(levels[i]-1.67))
        for j in [12,28,44,60]:
            hole=s.cut([head_faces[row,j],head_faces[row,(j+1)%96]])
            root=sum((Vector(s.v[i]) for i in hole),Vector())/len(hole)
            sign=1 if root.x>0 else -1
            sweep(s,[root,root+Vector((sign*.03,.055,-.07)),root+Vector((sign*.07,.09,-.15)),root+Vector((sign*.09,.075,-.17)),root+Vector((sign*.08,.055,-.15))],[.023,.023,.014,.009,.001],1,{'head':1},16,hole)
    obj=s.obj(col,mats,2)
    assert len(components(obj))==1,(name,'Body shell is disconnected',components(obj))
    obj['anatomy']='Continuous torso/hips/shoulders/limbs/palms/five digits/neck/face, with shared branch edges'
    obj['finger_bones']=0
    return obj

def detail_mesh(name,col,material,points,radii,w,sub=1,flat=1):
    s=Surface(name);sweep(s,points,radii,0,w,8,flat=flat);return s.obj(col,[material],sub)

def outfit(name,kind,accent,col):
    objects=[]
    for side in [-1,1]:
        s=Surface(name+'_TailoredPFD_'+str(side));rows=[]
        for iv in range(25):
            v=iv/24;row=[]
            for iu in range(19):
                u=iu/18;z=lerp(1.16,1.472-.075*u*u,v)
                rx=profile([(1.16,.143),(1.27,.168),(1.39,.195),(1.47,.18)],z)
                ry=profile([(1.16,.091),(1.27,.106),(1.39,.114),(1.47,.088)],z)
                x=side*(.011+u*(rx*.91-.011));y=-ry*math.sqrt(max(.01,1-(x/rx)**2))-.017
                y-=.009*math.sin(math.pi*u)*math.sin(math.pi*v)
                # Raised padding chambers and recessed seams are part of the fitted shell.
                y+=.0025*math.cos(v*6*math.pi)*math.sin(math.pi*u)**2
                row.append(s.vertex((x,y,z),torso_weights(z)))
            rows.append(row)
        for i in range(24):
            for j in range(18):s.face((rows[i][j],rows[i][j+1],rows[i+1][j+1],rows[i+1][j]))
        obj=s.obj(col,[M[accent]],2);solid=obj.modifiers.new('Sewn panel thickness','SOLIDIFY');solid.thickness=.011;objects.append(obj)
        # Piping follows the tailored perimeter and leaves room for shoulder rotation.
        for boundary in [[rows[i][0] for i in range(25)],[rows[i][-1] for i in range(25)],rows[0],rows[-1]]:
            points=[Vector(s.v[i])+Vector((0,-.0018,0)) for i in boundary]
            objects.append(detail_mesh('PFD_bound_edge',col,M['suit'],points,[.0022]*len(points),{'chest':1}))
        for zz in [1.23,1.345,1.41]:
            points=[(side*(.035+i*.008),-.128-.008*math.sin(i/10*math.pi),zz+.008*math.sin(i/10*math.pi)) for i in range(11)]
            objects.append(detail_mesh('Woven_reflective_strip',col,M['white'],points,[.0022]*11,{'chest':1},flat=.7))
        sn='L' if side<0 else 'R'
        # Molded toe ribs and instep channels follow the continuous boot surface.
        for i in range(5):
            y=-.135+i*.024
            points=[(side*.105+u*.041,y,.086+.019*(1-u*u)-i*.001) for u in [-1,-.5,0,.5,1]]
            objects.append(detail_mesh('Boot_grip_ridge',col,M['seam'],points,[.0022]*5,{'foot.'+sn:1},1))
    # Small interlocking zipper teeth, modeled as folded strips along the opening.
    for i in range(32):
        z=1.18+i*.0083;side=-1 if i%2 else 1
        objects.append(detail_mesh('Zipper_tooth',col,M['metal'],[(side*.003,-.13,z),(side*.007,-.131,z+.002),(side*.009,-.13,z+.003)],[.0015]*3,torso_weights(z),0))
    return objects

def face_details(name,kind,skin,col):
    objects=[]
    if kind in ['otter','capy']:
        s=Surface('Sculpted_nose_surface');previous=None
        for i in range(17):
            radius=max(.001,i/16);points=[]
            for j in range(48):
                angle=TAU*j/48;x=.027*radius*math.cos(angle);z=1.755+.012*radius*math.sin(angle)
                points.append((x,face_y(x,z,kind)-.002-.008*(1-radius*radius),z))
            loop=s.ring(points,{'head':1})
            if previous is None:s.cap(loop,0,{'head':1})
            else:s.bridge(previous,loop)
            previous=loop
        objects.append(s.obj(col,[M['nose_v3']],1))
    if kind=='robot':
        s=Surface('Recessed_visor');rows=[]
        for iz in range(13):
            z=1.755+iz*.0075;rows.append(s.ring([(x,face_y(x,z,kind)-.006,z) for x in [-.091+i*.0091 for i in range(21)]],{'head':1}))
        for i in range(12):
            for j in range(20):s.face((rows[i][j],rows[i][j+1],rows[i+1][j+1],rows[i+1][j]))
        obj=s.obj(col,[M['glass']],2);solid=obj.modifiers.new('Visor shell','SOLIDIFY');solid.thickness=.003;objects.append(obj)
    for side in [-1,1]:
        cx=side*(.044 if kind=='human' else .070);cz=1.804 if kind!='robot' else 1.815
        for label,rx,rz,material,depth in [('Sclera',.023,.0085,M['eye_v3'],.002),('Iris',.0075,.0075,M['lens'] if kind=='human' else M['teal'],.006),('Pupil',.0035,.0045,M['black'],.007)]:
            if kind=='robot' and label=='Sclera':material=M['teal']
            s=Surface(name+'_'+label);prev=None
            for ir in range(13):
                r=max(.001,ir/12);pts=[]
                for j in range(48):
                    a=TAU*j/48;x=cx+rx*math.cos(a)*r;z=cz+rz*math.sin(a)*r*(.8+.2*abs(math.sin(a)))
                    pts.append((x,face_y(x,z,kind)-depth-.003*(1-r*r),z))
                loop=s.ring(pts,{'head':1})
                if prev is not None:s.bridge(prev,loop)
                else:s.cap(loop,0,{'head':1})
                prev=loop
            objects.append(s.obj(col,[material],1))
        if kind!='robot':
            points=[]
            for j in range(49):
                a=TAU*j/48;x=cx+.024*math.cos(a);z=cz+.0095*math.sin(a)
                points.append((x,face_y(x,z,kind)-.003,z))
            objects.append(detail_mesh('Orbital_lid_margin',col,M[skin],points,[.0015]*49,{'head':1},1))
        if kind=='human':
            points=[]
            for i in range(15):
                x=cx-.028+i*.004;z=1.83+.006*math.sin(i/14*math.pi)
                points.append((x,face_y(x,z,kind)-.001,z))
            objects.append(detail_mesh('Sculpted_brow',col,M['hair_v3'],points,[.001+.001*math.sin(i/14*math.pi) for i in range(15)],{'head':1},1,flat=.65))
    if kind!='robot':
        for lip,z0 in [('Mouth',1.706)]:
            points=[]
            width=.030 if kind=='human' else .069
            for i in range(25):
                x=-width+2*width*i/24;z=z0+(.0015 if kind=='human' else .018)*(abs(x)/width)**2
                points.append((x,face_y(x,z,kind)-.0008,z))
            objects.append(detail_mesh(lip+'_lip_edge',col,M['lip_v3'] if kind=='human' else M['navy'],points,[(.0004 if kind=='human' else .0018)+.00025*math.sin(i/24*math.pi) for i in range(25)],{'head':1},1,flat=.4))
    if kind=='human':
        s=Surface(name+'_GroomedHair');prev=None
        for i in range(33):
            v=i/32;pts=[]
            for j in range(128):
                a=TAU*j/128;base=1.838+.067*max(0,-math.sin(a))-.035*max(0,math.sin(a))
                z=lerp(base,1.978,math.sin(v*math.pi/2));rx=profile(HEAD_X,min(z,1.972));ry=profile(HEAD_Y,min(z,1.972))
                groove=.0004*math.sin(a*31+v*9)+.0002*math.sin(a*67-v*3)
                expansion=(.003+groove)*math.sin(math.pi*(.15+.85*v))
                quiff=.019*gauss(math.cos(a),-.30,.7)*max(0,-math.sin(a))*math.sin(math.pi*v)**2
                taper=max(.025,1-clamp((v-.90)/.1)**2)
                pts.append(((rx+expansion)*math.cos(a)*taper,.01+(ry+expansion)*math.sin(a)*taper,z+quiff))
            loop=s.ring(pts,{'head':1})
            if prev is not None:s.bridge(prev,loop)
            prev=loop
        s.cap(prev,0,{'head':1});objects.append(s.obj(col,[M['hair_v3']],2))
        if name=='Zuri':
            s=Surface('Braided_updo');prev=None
            for i in range(25):
                t=i/24;z=1.885+t*.17;radius=.060*math.sin(math.pi*t)**.7+.003
                pts=[((radius+.004*math.sin(j/64*TAU*12+t*16))*math.cos(j/64*TAU),.070+radius*math.sin(j/64*TAU)*.80,z) for j in range(64)]
                loop=s.ring(pts,{'head':1})
                if prev is None:s.cap(loop,0,{'head':1})
                else:s.bridge(prev,loop)
                prev=loop
            s.cap(prev,0,{'head':1});objects.append(s.obj(col,[M['hair_v3']],2))
        else:
            pts=[(.103*math.cos(math.pi+i/40*math.pi),.008+.099*math.sin(math.pi+i/40*math.pi),1.89+.012*math.sin(i/40*math.pi)) for i in range(41)]
            objects.append(detail_mesh('Fitted_headband',col,M['teal'],pts,[.006]*41,{'head':1},1,flat=.22))
    return objects

report=[]
for name,kind,skin,accent,width,height in (ROSTER[:1] if '--hero' in sys.argv else ROSTER):
    col=bpy.data.collections[name];col.hide_render=False;col.hide_viewport=False;rig=rigs[name]
    rig.animation_data_clear();rig.location=(0,0,0);rig.rotation_euler=(0,0,0);rig.scale=(1,1,1)
    for pb in rig.pose.bones:
        pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
        for con in pb.constraints:con.influence=0
    body=connected_body(name,kind,skin,accent,col)
    base_vertices=len(body.data.vertices);base_faces=len(body.data.polygons)
    objs=[body]+outfit(name,kind,accent,col)+face_details(name,kind,skin,col)
    total=0
    for obj in objs:
        for v in obj.data.vertices:v.co.x*=width;v.co.z*=height
        obj.parent=rig
        total+=triangles(obj)
        mod=obj.modifiers.new('Body skeleton','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
    rig['static_fingers']='Four fingers and a thumb share each hand bone. No finger bones.'
    report.append({'name':name,'body_components':len(components(body)),'body_control_vertices':base_vertices,'body_control_faces':base_faces,'evaluated_source_triangles':total,'bone_count':len(rig.data.bones),'finger_bones':0,'method':'Connected branch topology; sculpted facial displacement; fitted clothing surfaces; subdivided control cages'})
    print('V3_RIDER',json.dumps(report[-1]),flush=True)
    # Keep finished high-resolution geometry cached on disk and free subdivision evaluation.
    for obj in objs:
        for mod in obj.modifiers:
            if mod.type=='SUBSURF':mod.show_viewport=False
    col.hide_render=True

scene['asset_revision']=3
scene['modeling_method']='Connected surface topology. No primitive objects are used in the character construction.'
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
# A neutral studio makes silhouette, anatomy and panel construction easy to inspect.
studio=bpy.data.collections.new('V3_Studio');scene.collection.children.link(studio)
floor=Surface('Studio_floor');floor.v=[(-200,-200,-.025),(200,-200,-.025),(200,200,-.025),(-200,200,-.025)];floor.w=[{}]*4;floor.face((0,1,2,3));floor.obj(studio,[mat('Studio_slate',(.055,.070,.081),.85)])
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for label,loc,power,size in [('Key',(-3,-4,5),700,3),('Fill',(3,-2,2.5),330,3),('Rim',(1,3,4),950,2)]:
    d=bpy.data.lights.new(label,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(label,d);studio.objects.link(o);o.location=loc;aim(o,(0,0,1.2))
d=bpy.data.cameras.new('V3_review');cam=bpy.data.objects.new('V3_review',d);studio.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=2.18;cam.location=(2.6,-7,2.5);aim(cam,(0,0,1.0))
scene.world.color=(.15,.15,.15)
bpy.data.collections['Kai'].hide_render=False
for obj in bpy.data.collections['Kai'].objects:
    for mod in obj.modifiers:
        if mod.type=='SUBSURF':mod.show_viewport=True
target=ROOT/'source'/('Hydro_Drift_Hero_v3.blend' if '--hero' in sys.argv else 'Hydro_Drift_Characters_v3.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
(ROOT/'characters_v3.json').write_text(json.dumps(report,indent=2))
if '--no-render' not in sys.argv:
    scene.render.filepath=str(ROOT/'previews/14_v3_rider_closeup.png');bpy.ops.render.render(write_still=True)
    d.ortho_scale=.48;cam.location=(.55,-2,1.90);aim(cam,(0,-.025,1.79));scene.render.filepath=str(ROOT/'previews/15_v3_face.png');bpy.ops.render.render(write_still=True)
print('V3_RIDERS_READY',flush=True)
