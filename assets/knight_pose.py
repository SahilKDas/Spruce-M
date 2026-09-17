"""Shared static riding pose; fingers have no individual joints."""
import bpy,math
from mathutils import Vector,Matrix
def solve(rig,first_name,second_name,target,hint):
    first=rig.pose.bones[first_name];second=rig.pose.bones[second_name]
    start=first.matrix.translation.copy();end=rig.matrix_world.inverted()@Vector(target)
    axis=end-start;distance=axis.length;axis.normalize();a=first.bone.length;b=second.bone.length
    along=(a*a-b*b+distance*distance)/(2*distance)
    toward=Vector(hint);bend=(toward-axis*toward.dot(axis)).normalized()
    hinge=start+axis*along+bend*math.sqrt(max(0,a*a-along*along))
    for bone,head,tail in [(first,start,hinge),(second,hinge,end)]:
        rest=bone.bone.matrix_local.to_3x3()
        rotation=(rest@Vector((0,1,0))).rotation_difference((tail-head).normalized()).to_matrix()@rest
        bone.matrix=Matrix.Translation(head)@rotation.to_4x4();bpy.context.view_layer.update()
def pose(rig):
    rig.location=(0,.20,.80-rig.data.bones['pelvis'].head_local.z*rig.scale.z)
    for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
    rig.pose.bones['spine'].rotation_euler.x=.15;rig.pose.bones['chest'].rotation_euler.x=.12
    rig.pose.bones['head'].rotation_euler.x=-.20
    bpy.context.view_layer.update()
    for side in [-1,1]:
        sn='L' if side<0 else 'R'
        solve(rig,'thigh.'+sn,'shin.'+sn,(side*.33,.29,.52),(side*.16,-1,.15))
        solve(rig,'upper_arm.'+sn,'forearm.'+sn,(side*.335,-.315,1.125),(side*1,.25,-.12))
        for prefix in ['hand.','foot.']:
            pb=rig.pose.bones[prefix+sn]
            rotation=pb.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
            if prefix=='hand.':rotation=Matrix.Rotation(-math.atan2(.835,.55),4,'X')@rotation
            pb.matrix=Matrix.Translation(pb.matrix.translation)@rotation
            bpy.context.view_layer.update()
    for frame in [1,2]:
        for pb in rig.pose.bones:
            pb.keyframe_insert('location',frame=frame);pb.keyframe_insert('rotation_euler',frame=frame);pb.keyframe_insert('scale',frame=frame)
    rig.animation_data.action.name='Riding'


def static_grip(mesh):
    """Shape fixed fingers around the grip with a continuous mesh bend.

    Neutral authoring meshes keep open hands. Riding meshes carry this fixed
    shape; no additional bones, weights, morph channels, or animation are added.
    """
    hand_groups={g.index for g in mesh.vertex_groups if g.name.startswith('hand.')}
    for vertex in mesh.data.vertices:
        if vertex.co.z>=.95 or abs(vertex.co.x)<.29:continue
        if not any(g.group in hand_groups and g.weight>.99 for g in vertex.groups):continue
        dy=vertex.co.y+.018;dz=vertex.co.z-.936
        along=-.55*dy-.835*dz
        across=.835*dy-.55*dz
        if along<=.085:continue
        angle=min(math.pi*.94,(along-.085)/.028)
        along=.085+.028*math.sin(angle)
        across+=.028*(1-math.cos(angle))
        vertex.co.y=-.018-.55*along+.835*across
        vertex.co.z=.936-.835*along-.55*across
    mesh.data.update()
