import bpy
import math

# AFTERFALL - LEAPER V0.8b POUNCE PREVIEW
# Context-safe Blender 5.2+ version.
# Fixes the "bpy.ops.object.select_all.poll() failed, context is incorrect" error.

RIG_NAME = "ARM_Leaper_GameRig_V07"
ACTION_NAME = "Leaper_Pounce_Preview"

rig = bpy.data.objects.get(RIG_NAME)
if not rig or rig.type != 'ARMATURE':
    raise RuntimeError(f"{RIG_NAME} not found. Run the V0.7 game rig first.")

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 96

if rig.animation_data is None:
    rig.animation_data_create()

old = bpy.data.actions.get(ACTION_NAME)
if old:
    if rig.animation_data.action == old:
        rig.animation_data.action = None
    bpy.data.actions.remove(old, do_unlink=True)

action = bpy.data.actions.new(ACTION_NAME)
rig.animation_data.action = action

for pb in rig.pose.bones:
    pb.rotation_mode = 'XYZ'
    pb.location = (0.0, 0.0, 0.0)
    pb.rotation_euler = (0.0, 0.0, 0.0)

def bone(name):
    return rig.pose.bones.get(name)

def set_rot(name, xyz_deg):
    pb = bone(name)
    if pb:
        pb.rotation_euler = tuple(math.radians(v) for v in xyz_deg)

def set_loc(name, xyz):
    pb = bone(name)
    if pb:
        pb.location = xyz

def neutral():
    for pb in rig.pose.bones:
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)

def key(frame):
    scene.frame_set(frame)
    for pb in rig.pose.bones:
        pb.keyframe_insert(data_path="location", frame=frame)
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)

neutral(); set_rot("head", (0,-3,0)); key(1)
set_rot("body",(0,1.5,0)); set_rot("head",(0,-5,0)); key(10)
neutral(); set_rot("head",(0,-3,0)); key(18)

neutral()
set_rot("body",(0,-4,0)); set_rot("head",(0,-9,0))
set_rot("FL_upper",(4,0,5)); set_rot("FR_upper",(-4,0,-5))
set_rot("ML_upper",(3,0,3)); set_rot("MR_upper",(-3,0,-3))
key(28)

neutral()
set_loc("root",(0,0,-0.16)); set_rot("body",(0,-8,0)); set_rot("head",(0,-13,0)); set_rot("rear_power",(0,9,0))
set_rot("FL_upper",(9,0,7)); set_rot("FR_upper",(-9,0,-7))
set_rot("FL_lower",(-18,0,0)); set_rot("FR_lower",(18,0,0))
set_rot("RL_upper",(-16,0,3)); set_rot("RR_upper",(16,0,-3))
set_rot("RL_lower",(30,0,0)); set_rot("RR_lower",(-30,0,0))
set_rot("ML_lower",(-12,0,0)); set_rot("MR_lower",(12,0,0))
key(38)

neutral()
set_loc("root",(0.55,0,0.35)); set_rot("body",(0,10,0)); set_rot("head",(0,-6,0)); set_rot("rear_power",(0,-10,0))
for n,r in {
    "FL_upper":(13,0,4),"FR_upper":(-13,0,-4),
    "ML_upper":(10,0,3),"MR_upper":(-10,0,-3),
    "RL_upper":(-10,0,2),"RR_upper":(10,0,-2),
    "FL_lower":(-25,0,0),"FR_lower":(25,0,0),
    "ML_lower":(-22,0,0),"MR_lower":(22,0,0),
    "RL_lower":(24,0,0),"RR_lower":(-24,0,0)
}.items(): set_rot(n,r)
key(46)

neutral()
set_loc("root",(1.85,0,1.25)); set_rot("body",(0,16,0)); set_rot("head",(0,-4,0)); set_rot("rear_power",(0,-8,0))
for n,r in {
    "FL_upper":(15,0,4),"FR_upper":(-15,0,-4),
    "ML_upper":(12,0,3),"MR_upper":(-12,0,-3),
    "RL_upper":(-12,0,2),"RR_upper":(12,0,-2),
    "FL_lower":(-30,0,0),"FR_lower":(30,0,0),
    "ML_lower":(-25,0,0),"MR_lower":(25,0,0),
    "RL_lower":(28,0,0),"RR_lower":(-28,0,0)
}.items(): set_rot(n,r)
key(56)

neutral()
set_loc("root",(3.15,0,-0.05)); set_rot("body",(0,-12,0)); set_rot("head",(0,-15,0)); set_rot("rear_power",(0,11,0))
set_rot("FL_upper",(-8,0,8)); set_rot("FR_upper",(8,0,-8))
set_rot("FL_lower",(18,0,0)); set_rot("FR_lower",(-18,0,0))
set_rot("ML_upper",(6,0,4)); set_rot("MR_upper",(-6,0,-4))
set_rot("RL_upper",(-7,0,3)); set_rot("RR_upper",(7,0,-3))
key(64)

neutral()
set_loc("root",(3.15,0,-0.10)); set_rot("body",(0,-5,0)); set_rot("head",(0,-8,0)); key(76)
neutral(); set_loc("root",(3.15,0,0)); set_rot("head",(0,-3,0)); key(88)
neutral(); set_loc("root",(3.15,0,0)); key(96)

scene.frame_set(1)
rig.hide_viewport=False
rig.hide_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active=rig

print("AFTERFALL Leaper V0.8b pounce preview created successfully.")
print("Frames 1-96. Put mouse over 3D Viewport and press Spacebar.")
