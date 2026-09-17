"""Build eight distinct knight riders from the reviewed anatomical armor construction."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from surface_modeling import Surface
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Knight_Kai.blend'))
scene=bpy.context.scene;base=bpy.data.collections['Kai_Realistic'];base.name='Kai'
base_objects=list(base.objects);base_rig=next(o for o in base_objects if o.type=='ARMATURE')
ROSTER=[
 ('Kai','Sun Knight',1,1,(.67,.11,.012),(.006,.26,.22),'sun'),
 ('Zuri','Tide Knight',.92,.98,(.006,.34,.30),(.56,.59,.55),'sail'),
 ('Riptide','Deepwater Knight',1.12,1.07,(.026,.09,.29),(.08,.22,.34),'fin'),
 ('Pip','Copper Scout',.86,.90,(.44,.16,.045),(.14,.055,.018),'low'),
 ('Marina','Rose Knight',.94,1.02,(.46,.035,.115),(.29,.09,.19),'wings'),
 ('Bolt','Iron Knight',1.17,1.05,(.06,.09,.12),(.60,.29,.022),'block'),
 ('Mochi','Bronze Guardian',1.22,.94,(.48,.44,.29),(.30,.14,.028),'crown'),
 ('Ink','Violet Knight',1,1.04,(.17,.035,.28),(.08,.10,.16),'split'),
]
report=[]
for name,title,width,height,color,helmet,crest in ROSTER:
    if name=='Kai':col=base;rig=base_rig
    else:
        col=bpy.data.collections.new(name);scene.collection.children.link(col)
        rig=base_rig.copy();rig.data=base_rig.data.copy();col.objects.link(rig)
        material_map={}
        for original in base_objects:
            if original.type!='MESH':continue
            obj=original.copy();obj.data=original.data.copy();col.objects.link(obj);obj.parent=rig
            for modifier in obj.modifiers:
                if modifier.type=='ARMATURE':modifier.object=rig
            for i,mat in enumerate(obj.data.materials):
                if not mat:continue
                if mat.name not in material_map:
                    new=mat.copy();new.name=name+' / '+mat.name
                    tone=color if 'orange enamel' in mat.name else helmet if 'teal enamel' in mat.name else None
                    if tone:
                        new.diffuse_color=(*tone,1);new.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*tone,1)
                    material_map[mat.name]=new
                obj.data.materials[i]=material_map[mat.name]
    rig.name=name+'_Rig';rig.scale=(width,width,height);rig['knight_title']=title
    # Each helmet has a manufactured crest or raised crown rather than a recolor alone.
    crest_mat=bpy.data.materials.new(name+' heraldic brass');crest_mat.diffuse_color=(*helmet,1);crest_mat.use_nodes=True
    shader=crest_mat.node_tree.nodes['Principled BSDF'];shader.inputs['Base Color'].default_value=(*helmet,1);shader.inputs['Metallic'].default_value=.72;shader.inputs['Roughness'].default_value=.34
    count=2 if crest in ['wings','split'] else 1
    for blade in range(count):
        surf=Surface(name+' '+crest+' crest');rows=[]
        for i in range(49):
            t=i/48;y=-.105+.235*t
            baseline=1.699+.052*math.sin(math.pi*t)
            lift={'sun':.035,'sail':.10,'fin':.14,'low':.015,'wings':.075,'block':.032,'crown':.045,'split':.09}[crest]*math.sin(math.pi*t)**.8
            cx=0 if count==1 else (-1 if blade==0 else 1)*(.052+.025*math.sin(math.pi*t))
            row=surf.ring([(cx+.006*math.cos(math.tau*j/12),y,baseline+lift*(.5+.5*math.sin(math.tau*j/12))) for j in range(12)],{'head':1})
            if rows:surf.bridge(rows[-1],row)
            else:surf.cap(row,0,{'head':1})
            rows.append(row)
        surf.cap(rows[-1],0,{'head':1});obj=surf.obj(col,[crest_mat],2);obj.parent=rig
        mod=obj.modifiers.new('Rigid helmet attachment','ARMATURE');mod.object=rig
    for obj in col.objects:
        if obj.type=='MESH':
            for modifier in obj.modifiers:
                if modifier.type=='MULTIRES':modifier.levels=0
                elif modifier.type=='SUBSURF':modifier.show_viewport=False
    col.hide_render=name!='Kai'
    report.append({'name':name,'title':title,'width':width,'height':height,'crest':crest,'bones':len(rig.data.bones),'finger_bones':0})
    print('KNIGHT_READY',name,flush=True)
scene['roster_revision']=4;scene['art_direction']='Eight armored knights; realistic anatomical foundation, forged plate silhouettes, fixed-finger gauntlets.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Knights.blend'),compress=True)
(ROOT/'knights.json').write_text(json.dumps(report,indent=2))
if '--no-render' not in sys.argv:
    studio=bpy.data.collections['Review_Studio']
    for i,(name,*_) in enumerate(ROSTER):
        col=bpy.data.collections[name];col.hide_render=False
        scene.view_layers[0].layer_collection.children[name].exclude=True
        for obj in col.objects:
            for modifier in obj.modifiers:
                if modifier.type=='MULTIRES':modifier.render_levels=1
        obj=bpy.data.objects.new(name+' review',None);studio.objects.link(obj);obj.instance_type='COLLECTION';obj.instance_collection=col;obj.location=((i-3.5)*1.03,0,0)
    camera=scene.camera;camera.location=(0,-13,2.7);camera.rotation_euler=(Vector((0,0,.9))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=8.7
    for obj in studio.objects:
        if obj.type=='LIGHT':obj.data.energy*=3;obj.data.size*=2
    scene.render.resolution_x=2400;scene.render.resolution_y=850;scene.cycles.samples=16
    scene.render.filepath=str(ROOT/'previews/25_knight_roster.png');bpy.ops.render.render(write_still=True)
print('KNIGHT_ROSTER_READY',flush=True)
