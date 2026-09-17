"""Anatomically fitted plate armor and a single-surface closed riding helm."""
import bpy,math
from mathutils import Vector
from surface_modeling import Surface,profile,gauss

def build_armor(col,extract,material,cord):
    steel=material('Satin forged steel',(.31,.36,.40),.29,.85)
    dark=material('Blackened steel',(.023,.037,.044),.38,.76)
    orange=material('Sun knight orange enamel',(.67,.11,.012),.40,.57)
    teal=material('Hydro teal enamel',(.006,.26,.22),.27,.62)
    gold=material('Warm brass engraving',(.40,.23,.062),.32,.77)
    orange.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.28
    pieces=[
      ('Left and right cuisses',lambda p:.56<p.z<.855 and abs(p.x)<.23,steel,.014),
      ('Knee poleyns',lambda p:.421<p.z<.55,orange,.020),
      ('Fitted greaves',lambda p:.13<p.z<.42,steel,.015),
      ('Swept pauldrons',lambda p:abs(p.x)>.155 and p.z>1.277 and p.z<1.443,orange,.027),
      ('Upper arm rerebraces',lambda p:abs(p.x)>.22 and 1.18<p.z<1.285,steel,.014),
      ('Elbow couters',lambda p:abs(p.x)>.25 and 1.10<p.z<1.184,orange,.019),
      ('Tapered vambraces',lambda p:abs(p.x)>.28 and .975<p.z<1.097,steel,.013),
      ('Fixed finger gauntlets',lambda p:abs(p.x)>.355 and p.z<.975,dark,.005),
    ]
    for name,region,mat,offset in pieces:
        obj=extract(name,region,mat,offset)
        obj['rigid_pair']={'Left and right cuisses':'thigh','Knee poleyns':'shin','Fitted greaves':'shin','Swept pauldrons':'upper_arm','Upper arm rerebraces':'upper_arm','Elbow couters':'forearm','Tapered vambraces':'forearm','Fixed finger gauntlets':'hand'}[name]
        smooth=obj.modifiers.new('Forged surface relaxation','SMOOTH');smooth.factor=.65;smooth.iterations=10 if name=='Cuirass' else 4
        obj.data.materials.append(gold)
        solid=obj.modifiers.new('Rolled plate edge','SOLIDIFY');solid.thickness=.006;solid.material_offset_rim=1
        bevel=obj.modifiers.new('Soft manufactured edges','BEVEL');bevel.width=.0018;bevel.segments=3
    for side in [-1,1]:
        boot=Surface('Formed sabaton');previous=None
        keys=[(.013,.072,.174,-.035),(.022,.075,.180,-.035),(.035,.075,.177,-.035),(.055,.071,.160,-.032),(.078,.060,.113,-.009),(.10,.049,.063,.039),(.13,.045,.054,.047),(.166,.045,.054,.047)]
        for i in range(41):
            z=.013+i/40*.153;rx=profile([(a,b) for a,b,c,d in keys],z);ry=profile([(a,c) for a,b,c,d in keys],z);cy=profile([(a,d) for a,b,c,d in keys],z)
            row=boot.ring([(side*.170+rx*math.cos(math.tau*j/64),cy+ry*math.sin(math.tau*j/64),z) for j in range(64)])
            if previous:boot.bridge(previous,row)
            else:boot.cap(row)
            previous=row
        obj=boot.obj(col,[steel],2);obj['rigid_bone']='foot.'+('L' if side<0 else 'R')
        solid=obj.modifiers.new('Shoe plate thickness','SOLIDIFY');solid.thickness=.003
    # Formed sheet-metal shells have their own smooth silhouette; they do not copy muscles.
    for name,zlo,zhi,xshape,yshape,mat in [
      ('Forged cuirass',.94,1.428,[(.94,.169),(1.04,.161),(1.14,.17),(1.24,.202),(1.32,.209),(1.37,.184),(1.405,.115),(1.428,.071)],[(.94,.130),(1.08,.142),(1.22,.158),(1.31,.163),(1.38,.123),(1.428,.074)],orange),
      ('Flared fauld skirt',.77,.954,[(.77,.199),(.82,.207),(.88,.193),(.954,.171)],[(.77,.147),(.82,.153),(.90,.140),(.954,.131)],steel)]:
        shell=Surface(name);previous=None
        for i in range(81):
            z=zlo+(zhi-zlo)*i/80;points=[]
            for j in range(128):
                angle=math.tau*j/128;x=profile(xshape,z)*math.cos(angle);sine=math.sin(angle)
                y=-.015+profile(yshape,z)*math.copysign(abs(sine)**.60,sine)
                if sine<0:y-=.018+.011*gauss(x,0,.033)*gauss(z,1.20,.19)
                points.append((x,y,z))
            row=shell.ring(points)
            if previous:shell.bridge(previous,row)
            if i in [0,80]:cord(name+' rolled rim',points+[points[0]],.0023,gold)
            previous=row
        obj=shell.obj(col,[mat],1);obj['rigid_bone']='chest' if name=='Forged cuirass' else 'pelvis'
        solid=obj.modifiers.new('Forged wall','SOLIDIFY');solid.thickness=.005
    # Build a true helmet shell with a pointed visor, brow line, and narrow eye openings.
    s=Surface('Closed armet helmet');rows=[]
    rx=[(1.425,.064),(1.46,.091),(1.51,.107),(1.57,.119),(1.62,.123),(1.66,.115),(1.70,.088),(1.742,.028),(1.753,.002)]
    ry=[(1.425,.105),(1.46,.151),(1.51,.181),(1.57,.187),(1.62,.182),(1.66,.159),(1.70,.120),(1.742,.040),(1.753,.003)]
    zs=sorted(set([1.425+i*.004 for i in range(83)]+[1.566,1.570,1.578,1.582,1.753]))
    zs=[z for z in zs if z<=1.753]
    for z in zs:
        row=[]
        for j in range(128):
            a=math.tau*j/128;x=profile(rx,z)*math.cos(a);y=.012+profile(ry,z)*math.sin(a)
            if y<0:y-=.022*gauss(x,0,.024)*gauss(z,1.535,.048)
            row.append(s.vertex((x,y,z)))
        rows.append(row)
    for i in range(len(rows)-1):
        for j in range(128):
            # Open slits are cut in the actual shell, backed by the wearer's face.
            if 1.570<=zs[i]<1.578 and (83<=j<=93 or 98<=j<=108):continue
            mat=0 if zs[i]<1.594 else 1
            if j in [94,95,96,97] and zs[i]>1.6:mat=2
            s.face((rows[i][j],rows[i][(j+1)%128],rows[i+1][(j+1)%128],rows[i+1][j]),mat)
    s.cap(rows[-1],1)
    obj=s.obj(col,[steel,teal,gold],1);obj['rigid_bone']='head'
    solid=obj.modifiers.new('Real helmet wall thickness','SOLIDIFY');solid.thickness=.003
    # Raised brow and visor rim follow the manufactured shell, emphasizing planes.
    for z in [1.565,1.585]:
        points=[]
        for j in range(65):
            a=math.pi+math.pi*j/64;x=profile(rx,z)*math.cos(a);y=.012+profile(ry,z)*math.sin(a)-.002
            y-=.022*gauss(x,0,.024)*gauss(z,1.535,.048)
            points.append((x,y,z))
        o=cord('Rolled visor rim',points,.0018,dark);o['rigid_bone']='head'
    # Breathing ports are recessed black vents, following the visor's curved front.
    for side in [-1,1]:
        for i in range(5):
            x=side*(.025+i*.013);z=1.526-i*.003
            y=.012-profile(ry,z)*math.sqrt(1-(x/profile(rx,z))**2)-.022*gauss(x,0,.024)*gauss(z,1.535,.048)-.002
            o=cord('Visor breathing vent',[(x,y,z-.004),(x,y-.001,z+.004)],.0015,dark);o['rigid_bone']='head'
    return obj
