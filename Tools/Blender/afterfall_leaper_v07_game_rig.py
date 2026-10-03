import bpy
from mathutils import Vector

# AFTERFALL - LEAPER V0.7 GAME RIG PREP
# Run on the manually refined V0.5 + V0.6 detail scene.
# This script:
# - creates a fresh mechanical game rig
# - uses the CURRENT object positions from the user's manual edits
# - rigidly bone-parents hard-surface pieces (no soft skin deformation)
# - leaves flexible cables/root details alone for now
# - hides older prototype armatures to avoid confusion
#
# Blender 5.2+
# SAFE: does not delete the robot meshes.

RIG_NAME = "ARM_Leaper_GameRig_V07"
ROOT_NAME = "LEAPER_ROOT"

root = bpy.data.objects.get(ROOT_NAME)
if not root:
    raise RuntimeError("LEAPER_ROOT not found. Open the refined Leaper scene first.")

def get(name):
    return bpy.data.objects.get(name)

def world_loc(name):
    o = get(name)
    if not o:
        return None
    return o.matrix_world.translation.copy()

def hide_old_armatures():
    for o in bpy.data.objects:
        if o.type == 'ARMATURE' and o.name != RIG_NAME:
            if "Leaper" in o.name or o.name.startswith("ARM_"):
                o.hide_viewport = True
                o.hide_render = True

def preserve_bone_parent(obj, armature, bone_name):
    if not obj or not armature:
        return
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = 'BONE'
    obj.parent_bone = bone_name
    obj.matrix_world = world

def preserve_object_parent(obj, parent):
    if not obj or not parent:
        return
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.parent_type = 'OBJECT'
    obj.matrix_world = world

old = get(RIG_NAME)
if old:
    bpy.data.objects.remove(old, do_unlink=True)

hide_old_armatures()

leg_ids = ["FL","FR","ML","MR","RL","RR"]
joint_data = {}

for leg in leg_ids:
    hip = world_loc(f"{leg}_HipJoint")
    knee = world_loc(f"{leg}_KneeJoint")
    ankle = world_loc(f"{leg}_AnkleJoint")
    claw = get(f"{leg}_MainClaw")
    if not all((hip, knee, ankle, claw)):
        raise RuntimeError(f"Missing required objects for {leg} leg.")
    claw_mid = claw.matrix_world.translation.copy()
    direction = claw_mid - ankle
    if direction.length < 0.001:
        direction = Vector((0.25,0,0))
    toe = claw_mid + direction.normalized() * max(direction.length, 0.18)
    joint_data[leg] = (hip, knee, ankle, toe)

thorax = get("Thorax_Core")
head_obj = get("Head_Base")
rear_obj = get("Rear_Housing")

body_center = thorax.matrix_world.translation.copy() if thorax else root.matrix_world.translation.copy()
head_center = head_obj.matrix_world.translation.copy() if head_obj else body_center + Vector((1.0,0,-0.1))
rear_center = rear_obj.matrix_world.translation.copy() if rear_obj else body_center + Vector((-1.0,0,0.1))

bpy.ops.object.armature_add(enter_editmode=True, location=(0,0,0))
rig = bpy.context.object
rig.name = RIG_NAME
rig.show_in_front = True
rig.data.name = "Leaper_GameRig_V07_Data"

eb = rig.data.edit_bones
eb.remove(eb[0])

b_root = eb.new("root")
b_root.head = body_center + Vector((0,0,-1.25))
b_root.tail = body_center + Vector((0,0,-0.55))

b_body = eb.new("body")
b_body.head = body_center + Vector((0,0,-0.35))
b_body.tail = body_center + Vector((0,0,0.45))
b_body.parent = b_root

b_head = eb.new("head")
b_head.head = body_center + Vector((0.55,0,-0.05))
b_head.tail = head_center + Vector((0.35,0,0))
b_head.parent = b_body

b_rear = eb.new("rear_power")
b_rear.head = body_center + Vector((-0.45,0,0))
b_rear.tail = rear_center + Vector((-0.45,0,0.15))
b_rear.parent = b_body

for leg in leg_ids:
    hip, knee, ankle, toe = joint_data[leg]

    upper = eb.new(f"{leg}_upper")
    upper.head = hip
    upper.tail = knee
    upper.parent = b_body

    lower = eb.new(f"{leg}_lower")
    lower.head = knee
    lower.tail = ankle
    lower.parent = upper
    lower.use_connect = False

    foot = eb.new(f"{leg}_foot")
    foot.head = ankle
    foot.tail = toe
    foot.parent = lower
    foot.use_connect = False

bpy.ops.object.mode_set(mode='OBJECT')
preserve_object_parent(rig, root)

body_names = [
    "Thorax_Core","Armor_Center","Rear_Housing",
    "TopPlate_0","TopPlate_1","TopPlate_2",
    "SideArmor_F_-1","SideArmor_F_1","SideArmor_R_-1","SideArmor_R_1",
    "SpineVent_0","SpineVent_1","SpineVent_2","SpineVent_3","SpineVent_4",
    "Belly_Core","Belly_Core_Ring",
    "V06_SensorChin",
    "V06_TopScale_0","V06_TopScale_1","V06_TopScale_2",
    "V06_TopScale_3","V06_TopScale_4","V06_TopScale_5",
    "V06_BellyRib_-1","V06_BellyRib_1",
    "V06_RearFin_0","V06_RearFin_1","V06_RearFin_2",
    "V06_StatusRing_-1","V06_StatusRing_1",
]

head_names = [
    "Head_Base","Head_Armor","Sensor_Main","Sensor_Main_Ring",
    "Sensor_Aux_0","Sensor_Aux_1","Sensor_Aux_2","Sensor_Aux_3",
    "Brow_-1","Brow_1",
    "MandibleArm_-1","MandibleArm_1",
    "MandibleClaw_-1","MandibleClaw_1",
    "V06_CheekGuard_L","V06_CheekGuard_R",
    "WP_SENSOR",
]

rear_names = [
    "JumpActuator_-1","JumpActuator_1",
    "JumpPiston_-1","JumpPiston_1",
    "JumpCore_-1","JumpCore_1",
    "JumpCoreRing_-1","JumpCoreRing_1",
    "JumpArmor_-1","JumpArmor_1",
    "V06_ActuatorGuardA_-1","V06_ActuatorGuardA_1",
    "V06_ActuatorGuardB_-1","V06_ActuatorGuardB_1",
    "V06_JumpFin_-1_0","V06_JumpFin_-1_1","V06_JumpFin_-1_2",
    "V06_JumpFin_1_0","V06_JumpFin_1_1","V06_JumpFin_1_2",
    "WP_JUMP_L","WP_JUMP_R",
]

for n in body_names:
    preserve_bone_parent(get(n), rig, "body")
for n in head_names:
    preserve_bone_parent(get(n), rig, "head")
for n in rear_names:
    preserve_bone_parent(get(n), rig, "rear_power")

shoulder_map = {
    "Shoulder_FL":"FL_upper",
    "Shoulder_FR":"FR_upper",
    "Shoulder_RL":"RL_upper",
    "Shoulder_RR":"RR_upper",
    "V06_FrontShoulderBlade_1":"FL_upper",
    "V06_FrontShoulderBlade_-1":"FR_upper",
    "V06_RearShoulderBlade_1":"RL_upper",
    "V06_RearShoulderBlade_-1":"RR_upper",
}
for n,bone in shoulder_map.items():
    preserve_bone_parent(get(n), rig, bone)

for leg in leg_ids:
    upper_names = [
        f"{leg}_HipJoint",
        f"{leg}_Upper",
        f"{leg}_Hydraulic",
        f"{leg}_UpperArmor",
    ]
    lower_names = [
        f"{leg}_KneeJoint",
        f"{leg}_Lower",
        f"{leg}_KneeArmor",
        f"V06_{leg}_LowerHydraulic",
        f"V06_{leg}_ShinArmor",
    ]
    foot_names = [
        f"{leg}_AnkleJoint",
        f"{leg}_MainClaw",
        f"{leg}_SideClawA",
        f"{leg}_SideClawB",
    ]
    for n in upper_names:
        preserve_bone_parent(get(n), rig, f"{leg}_upper")
    for n in lower_names:
        preserve_bone_parent(get(n), rig, f"{leg}_lower")
    for n in foot_names:
        preserve_bone_parent(get(n), rig, f"{leg}_foot")

preserve_bone_parent(get("WP_FRONT_LEFT_KNEE"), rig, "FL_upper")
preserve_bone_parent(get("WP_FRONT_RIGHT_KNEE"), rig, "FR_upper")
preserve_bone_parent(get("WP_BELLY_CORE"), rig, "body")

rig["RigVersion"] = "V0.7"
rig["RigType"] = "Rigid mechanical prototype"
rig["Target"] = "Unreal Engine mobile prototype"
rig["Notes"] = "Bone-parented hard surface. Curves/cables left unrigged for prototype."

bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='POSE')
for pb in rig.pose.bones:
    pb.rotation_mode = 'XYZ'
bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig

print("AFTERFALL Leaper V0.7 game rig created successfully.")
print("Next: select ARM_Leaper_GameRig_V07 and switch to Pose Mode to test legs.")
