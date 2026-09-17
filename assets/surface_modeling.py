"""Surface modeling utilities. Control vertices and connected faces, no mesh primitives."""
import bpy, bmesh, math
from mathutils import Vector
TAU=math.tau

def lerp(a,b,t):return a+(b-a)*t
def clamp(x,a=0,b=1):return max(a,min(b,x))
def gauss(x,c,s):return math.exp(-((x-c)/s)**2)
def profile(points,t):
    if t<=points[0][0]:return points[0][1]
    for i,((a,x),(b,y)) in enumerate(zip(points,points[1:])):
        if t<=b:
            u=(t-a)/(b-a)
            prev=points[max(0,i-1)];nxt=points[min(len(points)-1,i+2)]
            m0=(y-prev[1])/(b-prev[0]);m1=(nxt[1]-x)/(nxt[0]-a)
            return (2*u**3-3*u*u+1)*x+(u**3-2*u*u+u)*(b-a)*m0+(-2*u**3+3*u*u)*y+(u**3-u*u)*(b-a)*m1
    return points[-1][1]

class Surface:
    def __init__(self,name):self.name=name;self.v=[];self.f=[];self.m=[];self.w=[]
    def vertex(self,p,w=None):
        self.v.append(tuple(p));self.w.append(w or {});return len(self.v)-1
    def face(self,ids,mat=0):
        self.f.append(tuple(ids));self.m.append(mat);return len(self.f)-1
    def ring(self,points,w=None):return [self.vertex(p,w) for p in points]
    def align(self,a,b):
        best=None;error=1e20
        for order in [b,list(reversed(b))]:
            start=min(range(len(order)),key=lambda j:(Vector(self.v[a[0]])-Vector(self.v[order[j]])).length_squared)
            seq=order[start:]+order[:start]
            d=sum((Vector(self.v[a[i]])-Vector(self.v[seq[int(i*len(b)/len(a))]])).length_squared for i in range(len(a)))
            if d<error:error=d;best=seq
        return best
    def bridge(self,a,b,mat=0,align=False):
        if align:b=self.align(a,b)
        i=j=0;na,nb=len(a),len(b)
        while i<na or j<nb:
            fa=(i+1)/na;fb=(j+1)/nb
            if abs(fa-fb)<1e-8:
                self.face((a[i%na],a[(i+1)%na],b[(j+1)%nb],b[j%nb]),mat);i+=1;j+=1
            elif fa<fb:self.face((a[i%na],a[(i+1)%na],b[j%nb]),mat);i+=1
            else:self.face((a[i%na],b[(j+1)%nb],b[j%nb]),mat);j+=1
        return b
    def cap(self,loop,mat=0,w=None):
        p=sum((Vector(self.v[i]) for i in loop),Vector())/len(loop)
        center=self.vertex(p,w if w is not None else self.w[loop[0]])
        for i in range(len(loop)):self.face((loop[i],loop[(i+1)%len(loop)],center),mat)
    def cut(self,faces):
        edges={}
        for index in faces:
            face=self.f[index]
            if face is None:continue
            for a,b in zip(face,face[1:]+face[:1]):
                e=tuple(sorted((a,b)));edges[e]=edges.get(e,0)+1
            self.f[index]=None
        adjacent={}
        for (a,b),count in edges.items():
            if count==1:adjacent.setdefault(a,[]).append(b);adjacent.setdefault(b,[]).append(a)
        if not adjacent:return []
        start=min(adjacent);loop=[start];previous=None;current=start
        while True:
            choices=[j for j in adjacent[current] if j!=previous]
            nxt=choices[0]
            if nxt==start:break
            loop.append(nxt);previous,current=current,nxt
            if len(loop)>len(adjacent):raise RuntimeError('Invalid surface boundary '+self.name)
        return loop
    def grid_cap(self,cx,cy,z,rx,ry,nx,ny,holes=(),w=None,mat=0):
        rows=[];faces={}
        for iy in range(ny+1):
            row=[];y=-1+2*iy/ny
            for ix in range(nx+1):
                x=-1+2*ix/nx
                row.append(self.vertex((cx+rx*x*math.sqrt(1-y*y/2),cy+ry*y*math.sqrt(1-x*x/2),z),w))
            rows.append(row)
        for iy in range(ny):
            for ix in range(nx):
                faces[ix,iy]=self.face((rows[iy][ix],rows[iy][ix+1],rows[iy+1][ix+1],rows[iy+1][ix]),mat)
        outer=rows[0][:]+[rows[i][-1] for i in range(1,ny+1)]+list(reversed(rows[-1][:-1]))+[rows[i][0] for i in range(ny-1,0,-1)]
        loops=[]
        for x0,x1,y0,y1 in holes:loops.append(self.cut([faces[x,y] for y in range(y0,y1) for x in range(x0,x1)]))
        return outer,loops
    def obj(self,collection,materials,sub=0):
        # Drop unused vertices left inside modeled branch openings.
        used=sorted({i for f in self.f if f is not None for i in f});lookup={v:i for i,v in enumerate(used)}
        mesh=bpy.data.meshes.new(self.name+'_Topology')
        faces=[tuple(lookup[i] for i in f) for f in self.f if f is not None]
        mesh.from_pydata([self.v[i] for i in used],[],faces);mesh.update()
        obj=bpy.data.objects.new(self.name,mesh);collection.objects.link(obj)
        for mat in materials:mesh.materials.append(mat)
        for poly,mat in zip(mesh.polygons,[m for f,m in zip(self.f,self.m) if f is not None]):poly.material_index=mat;poly.use_smooth=True
        groups={}
        for new,old in enumerate(used):
            weights=self.w[old];total=sum(weights.values())
            for name,weight in weights.items():
                if weight<.00001:continue
                group=groups.get(name)
                if group is None:group=obj.vertex_groups.new(name=name);groups[name]=group
                group.add([new],weight/total,'REPLACE')
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
        uv=mesh.uv_layers.new(name='SurfaceUV')
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                p=mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv=(p.x*2+p.y,p.z*2)
        if sub:
            mod=obj.modifiers.new('Sculpt surface subdivision','SUBSURF');mod.levels=sub;mod.render_levels=sub
        obj['construction']='Authored continuous surface control cage; shared vertices at anatomical branches'
        return obj

def loft(surface,sections,segments=32,axis='Z',mat=0,previous=None,close=True):
    first=None;prev=previous
    for center,rx,ry,w in sections:
        pts=[]
        for j in range(segments):
            a=TAU*j/segments
            if axis=='Z':p=(center[0]+rx*math.cos(a),center[1]+ry*math.sin(a),center[2])
            elif axis=='Y':p=(center[0]+rx*math.cos(a),center[1],center[2]+ry*math.sin(a))
            pts.append(p)
        loop=surface.ring(pts,w)
        if prev is not None:loop=surface.bridge(prev,loop,mat,align=True)
        elif close:surface.cap(loop,mat,w)
        if first is None:first=loop
        prev=loop
    if close:surface.cap(prev,mat)
    return prev

def sweep(surface,points,radii,mat=0,w=None,segments=12,previous=None,flat=1):
    prev=previous
    for i,p in enumerate(points):
        p=Vector(p);direction=(Vector(points[min(len(points)-1,i+1)])-Vector(points[max(0,i-1)])).normalized()
        u=direction.cross(Vector((0,1,0)))
        if u.length<.01:u=direction.cross(Vector((1,0,0)))
        u.normalize();v=direction.cross(u).normalized()
        loop=surface.ring([p+radii[i]*(u*math.cos(TAU*j/segments)+v*math.sin(TAU*j/segments)*flat) for j in range(segments)],w)
        if prev is not None:loop=surface.bridge(prev,loop,mat,align=True)
        else:surface.cap(loop,mat,w)
        prev=loop
    surface.cap(prev,mat,w)
    return prev

def components(obj):
    adjacency=[[] for _ in obj.data.vertices]
    for e in obj.data.edges:a,b=e.vertices;adjacency[a].append(b);adjacency[b].append(a)
    seen=set();counts=[]
    for seed in range(len(adjacency)):
        if seed in seen:continue
        stack=[seed];seen.add(seed);count=0
        while stack:
            i=stack.pop();count+=1
            for j in adjacency[i]:
                if j not in seen:seen.add(j);stack.append(j)
        counts.append(count)
    return sorted(counts,reverse=True)

def apply_modifiers(obj):
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    for mod in list(obj.modifiers):
        if mod.type!='ARMATURE':bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)

def triangles(obj):
    dep=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dep);mesh=ev.to_mesh();mesh.calc_loop_triangles();count=len(mesh.loop_triangles);ev.to_mesh_clear();return count
