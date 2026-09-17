"""Export revision 4 knights with static fingers and anatomically solved riding poses."""
import bpy,bmesh,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from surface_modeling import apply_modifiers,triangles,components
OUT=ROOT.parent/'game/art';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Hydro_Drift_Knights.blend'))
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=2;scene.frame_set(1)
report=[]
def select(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs:obj.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
def export(path,mesh,rig,animated=False):
    select([mesh,rig])
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_skins=True,export_def_bones=True,export_animations=animated,export_animation_mode='ACTIVE_ACTIONS',export_nla_strips_merged_animation_name='Riding',export_force_sampling=True,export_frame_range=True)
from knight_pose import pose,static_grip

for name in ['Kai','Zuri','Riptide','Pip','Marina','Bolt','Mochi','Ink']:
    for lc in scene.view_layers[0].layer_collection.children:lc.exclude=lc.name!=name
    col=bpy.data.collections[name];original_rig=next(o for o in col.objects if o.type=='ARMATURE')
    temp=bpy.data.collections.new('_Export');scene.collection.children.link(temp)
    rig=original_rig.copy();rig.data=original_rig.data.copy();rig.animation_data_clear();temp.objects.link(rig)
    meshes=[]
    for original in list(col.objects):
        if original.type!='MESH':continue
        obj=original.copy();obj.data=original.data.copy();temp.objects.link(obj);obj.parent=rig
        for modifier in obj.modifiers:
            modifier.show_viewport=True
            if modifier.type=='ARMATURE':modifier.object=rig
            if modifier.type=='MULTIRES':modifier.levels=min(2,modifier.total_levels)
        apply_modifiers(obj);meshes.append(obj)
    select(meshes);bpy.ops.object.join();mesh=bpy.context.object;mesh.name=name+'_Knight'
    mesh.data.validate();mesh.data.update()
    normalized=0
    for vertex in mesh.data.vertices:
        total=sum(g.weight for g in vertex.groups)
        if total>0 and abs(total-1)>.00001:
            for group in list(vertex.groups):mesh.vertex_groups[group.group].add([vertex.index],group.weight/total,'REPLACE')
            normalized+=1
    unweighted=sum(not v.groups for v in mesh.data.vertices)
    invalid=sum(abs(sum(g.weight for g in v.groups)-1)>.002 for v in mesh.data.vertices)
    assert unweighted==0 and invalid==0,(name,unweighted,invalid)
    assert not any('finger' in b.name.lower() or 'thumb' in b.name.lower() for b in rig.data.bones)
    count=triangles(mesh);export(ROOT/'exports'/f'{name}.glb',mesh,rig)
    lods=[]
    for i,target in enumerate([160000,22000],1):
        obj=mesh.copy();obj.data=mesh.data.copy();temp.objects.link(obj)
        obj.data.calc_loop_triangles();mod=obj.modifiers.new('Distance detail budget','DECIMATE');mod.ratio=min(1,target/len(obj.data.loop_triangles))
        select([obj]);bpy.ops.object.modifier_apply(modifier=mod.name)
        export(ROOT/'exports'/f'{name}_LOD{i}.glb',obj,rig);lods.append(obj)
    for obj in lods:static_grip(obj)
    pose(rig)
    for suffix,obj in zip(['near','far'],lods):export(OUT/f'{name}_{suffix}.glb',obj,rig,True)
    report.append({'name':name,'source_glb_triangles':count,'near_target':160000,'far_target':22000,'bones':len(rig.data.bones),'finger_bones':0,'unweighted_vertices':unweighted,'invalid_weight_sums':invalid,'weights_normalized_after_modifiers':normalized,'theme':'knight'})
    print('EXPORTED_KNIGHT',name,count,flush=True)
    for obj in list(temp.objects):bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.collections.remove(temp)
(ROOT/'knight_validation.json').write_text(json.dumps(report,indent=2))
(OUT/'runtime_manifest.json').write_text(json.dumps({'revision':4,'theme':'knights','riders':report},indent=2))
print('KNIGHT_EXPORTS_READY',flush=True)
