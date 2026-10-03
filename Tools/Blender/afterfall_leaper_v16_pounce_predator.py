import bpy, math
from mathutils import Vector, Matrix, Quaternion

# AFTERFALL - LEAPER V1.6 "POUNCE PREDATOR"
# Run on top of the V1.5 Predator Refit scene.
# Non-destructive to the armature rest pose:
# - creates a V1.6 crouched idle Action for preview/export
# - slightly restores body mass without returning to the bulky V1.4 look
# - covers exposed round joints with angular dark armor
# - replaces bright blocky scan lights with a thin hostile sensor slit
# - keeps weak points matte grey until gameplay reveals them
#
# Blender 5.2+

ROOT_NAME = "LEAPER_ROOT"
RIG_NAME = "ARM_Leaper_Final"
ACTION_NAME = "Leaper_V16_PredatorIdle"

root = bpy.data.objects.get(ROOT_NAME)
rig = bpy.data.objects.get(RIG_NAME)

if not root:
    raise RuntimeError("LEAPER_ROOT not found. Open Leaper_Standard_Final.blend first.")
if not rig or rig.type != 'ARMATURE':
    raise RuntimeError("ARM_Leaper_Final armature not found.")
if not bpy.data.objects.get("WP_Eye_Cover"):
    raise RuntimeError("V1.3 weak-point parts were not found. Run the weak-point patch first.")

scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()

def obj(name):
    return bpy.data.objects.get(name)

def mat(name, base, metal=0.0, rough=0.45, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    if not p:
        p = m.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (*base, 1.0)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    if "Emission Strength" in p.inputs:
        p.inputs["Emission Strength"].default_value = 0.0
    if emission is not None:
        if "Emission Color" in p.inputs:
            p.inputs["Emission Color"].default_value = (*emission, 1.0)
        if "Emission Strength" in p.inputs:
            p.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*base, 1.0)
    return m

def setmat(o, m):
    if o and o.type == 'MESH':
        o.data.materials.clear()
        o.data.materials.append(m)
        o.color = m.diffuse_color

def cleanup_v16():
    for o in list(bpy.data.objects):
        if o.name.startswith("V16_"):
            bpy.data.objects.remove(o, do_unlink=True)

def rigid_skin(o, bone_name):
    if not o or o.type != 'MESH':
        return
    world = o.matrix_world.copy()
    for mod in list(o.modifiers):
        if mod.type == 'ARMATURE':
            o.modifiers.remove(mod)
    for vg in list(o.vertex_groups):
        o.vertex_groups.remove(vg)
    vg = o.vertex_groups.new(name=bone_name)
    if len(o.data.vertices):
        vg.add(range(len(o.data.vertices)), 1.0, 'REPLACE')
    am = o.modifiers.new("Leaper_Final_Rig", "ARMATURE")
    am.object = rig
    o.parent = rig
    o.parent_type = 'OBJECT'
    o.matrix_world = world

def bone_world_matrix(bone_name):
    pb = rig.pose.bones.get(bone_name)
    if not pb:
        return None
    return rig.matrix_world @ pb.matrix

def armor_box(name, bone_name, scale=(0.20, 0.13, 0.09), offset=(0,0,0), material=None):
    bm = bone_world_matrix(bone_name)
    if bm is None:
        return None
    loc = bm.translation + (bm.to_quaternion() @ Vector(offset))
    rot = bm.to_quaternion()
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = rot
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = o.modifiers.new("V16_Bevel", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 2
    bpy.context.view_layer.objects.active = o
    try:
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception:
        pass
    if material:
        setmat(o, material)
    rigid_skin(o, bone_name)
    return o

def thin_box(name, parent_bone, world_center, world_quat, scale, material):
    bpy.ops.mesh.primitive_cube_add(location=world_center)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = world_quat
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = o.modifiers.new("V16_Bevel", "BEVEL")
    bevel.width = 0.008
    bevel.segments = 2
    bpy.context.view_layer.objects.active = o
    try:
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception:
        pass
    setmat(o, material)
    rigid_skin(o, parent_bone)
    return o

def scale_about_world(o, center, factor):
    if not o or o.type != 'MESH':
        return
    loc, rot, scl = o.matrix_world.decompose()
    delta = loc - center
    new_loc = center + Vector((delta.x * factor.x, delta.y * factor.y, delta.z * factor.z))
    new_scl = Vector((scl.x * factor.x, scl.y * factor.y, scl.z * factor.z))
    o.matrix_world = (
        Matrix.Translation(new_loc)
        @ rot.to_matrix().to_4x4()
        @ Matrix.Diagonal((new_scl.x, new_scl.y, new_scl.z, 1.0))
    )

def pb(name):
    return rig.pose.bones.get(name)

def set_rot(name, x=0.0, y=0.0, z=0.0):
    b = pb(name)
    if not b:
        return
    b.rotation_mode = 'XYZ'
    b.rotation_euler = (math.radians(x), math.radians(y), math.radians(z))

def set_loc(name, x=0.0, y=0.0, z=0.0):
    b = pb(name)
    if b:
        b.location = (x, y, z)

def key_bone(name, frame):
    b = pb(name)
    if not b:
        return
    b.keyframe_insert(data_path="location", frame=frame)
    b.keyframe_insert(data_path="rotation_euler", frame=frame)

cleanup_v16()

M_BLACK = mat("LEAP_V16_BlackArmor", (0.008, 0.010, 0.014), 0.92, 0.23)
M_GUN = mat("LEAP_V16_Gunmetal", (0.022, 0.026, 0.032), 0.94, 0.22)
M_WP = mat("LEAP_V16_WeakPoint_DormantGrey", (0.105, 0.110, 0.118), 0.80, 0.31)
M_SCAN = mat("LEAP_SIGNAL_Scan_White", (0.75, 0.76, 0.72), 0.03, 0.14, (1.0, 0.95, 0.80), 5.0)
M_ALERT = mat("LEAP_SIGNAL_Alert_Yellow", (0.55, 0.42, 0.08), 0.03, 0.15, (1.0, 0.62, 0.05), 7.0)
M_ATTACK = mat("LEAP_SIGNAL_Attack_Red", (0.35, 0.02, 0.015), 0.03, 0.14, (1.0, 0.025, 0.012), 10.0)

for name in ("WP_Eye_Cover", "WP_FrontL_Cover", "WP_FrontR_Cover", "WP_RearL_Cover", "WP_RearR_Cover"):
    setmat(obj(name), M_WP)

for name in ("Core_Body", "TopArmor", "BackArmor", "Armor_L", "Armor_R"):
    setmat(obj(name), M_BLACK)

if str(root.get("PredatorRefitVersion", "")) != "1.6":
    core = obj("Core_Body")
    if core:
        body_center = core.matrix_world.translation.copy()
        grow = Vector((1.10, 1.08, 1.08))
        for name in (
            "Core_Body", "TopArmor", "BackArmor", "Armor_L", "Armor_R",
            "WeakPort_L", "WeakPort_R",
            "WeakPortFrame_L_Top", "WeakPortFrame_L_Bottom",
            "WeakPortFrame_R_Top", "WeakPortFrame_R_Bottom",
        ):
            scale_about_world(obj(name), body_center, grow)

if rig.animation_data is None:
    rig.animation_data_create()

old = bpy.data.actions.get(ACTION_NAME)
if old:
    if rig.animation_data.action == old:
        rig.animation_data.action = None
    bpy.data.actions.remove(old, do_unlink=True)

action = bpy.data.actions.new(ACTION_NAME)
rig.animation_data.action = action

pose_bones = (
    "root", "body", "head",
    "FL_upper", "FL_lower", "FL_foot",
    "FR_upper", "FR_lower", "FR_foot",
    "RL_upper", "RL_lower", "RL_foot",
    "RR_upper", "RR_lower", "RR_foot",
)
for name in pose_bones:
    b = pb(name)
    if b:
        b.rotation_mode = 'XYZ'
        b.location = (0.0, 0.0, 0.0)
        b.rotation_euler = (0.0, 0.0, 0.0)

set_loc("root", 0.0, 0.0, -0.12)
set_rot("body", 0.0, -7.0, 0.0)
set_loc("head", 0.10, 0.0, -0.09)
set_rot("head", 0.0, -14.0, 0.0)

set_rot("FL_upper", 10.0, 0.0, 10.0)
set_rot("FR_upper", -10.0, 0.0, -10.0)
set_rot("FL_lower", -20.0, 0.0, 0.0)
set_rot("FR_lower", 20.0, 0.0, 0.0)

set_rot("RL_upper", -15.0, 0.0, 7.0)
set_rot("RR_upper", 15.0, 0.0, -7.0)
set_rot("RL_lower", 28.0, 0.0, 0.0)
set_rot("RR_lower", -28.0, 0.0, 0.0)

for frame in (1, 30):
    scene.frame_set(frame)
    for name in pose_bones:
        key_bone(name, frame)

# Blender 5.2 uses the layered Action API; the legacy action.fcurves
# collection is no longer available here. Both keyframes hold the same pose,
# so the stance remains visually static without forcing interpolation.
scene.frame_start = 1
scene.frame_end = 30
scene.frame_set(1)
bpy.context.view_layer.update()

joint_specs = {
    "FL_upper": ((0.21, 0.14, 0.095), (0.0, 0.0, 0.02)),
    "FL_lower": ((0.18, 0.12, 0.085), (0.0, 0.0, 0.00)),
    "FR_upper": ((0.21, 0.14, 0.095), (0.0, 0.0, 0.02)),
    "FR_lower": ((0.18, 0.12, 0.085), (0.0, 0.0, 0.00)),
    "RL_upper": ((0.22, 0.14, 0.100), (0.0, 0.0, 0.02)),
    "RL_lower": ((0.19, 0.12, 0.090), (0.0, 0.0, 0.00)),
    "RR_upper": ((0.22, 0.14, 0.100), (0.0, 0.0, 0.02)),
    "RR_lower": ((0.19, 0.12, 0.090), (0.0, 0.0, 0.00)),
}
for bone_name, (scale, offset) in joint_specs.items():
    armor_box("V16_JointArmor_" + bone_name, bone_name, scale, offset, M_BLACK)

eye = obj("Eye_Lens")
core = obj("Core_Body")
if eye and core:
    eye_pos = eye.matrix_world.translation.copy()
    body_pos = core.matrix_world.translation.copy()
    forward = eye_pos - body_pos
    if forward.length < 0.001:
        forward = Vector((1, 0, 0))
    forward.normalize()
    up0 = Vector((0, 0, 1))
    side = up0.cross(forward)
    if side.length < 0.001:
        side = Vector((0, 1, 0))
    side.normalize()
    up = forward.cross(side).normalized()
    basis = Matrix((
        (forward.x, side.x, up.x),
        (forward.y, side.y, up.y),
        (forward.z, side.z, up.z),
    ))
    q = basis.to_quaternion()
    center = eye_pos - forward * 0.035 + up * 0.105
    thin_box("V16_SensorSlit", "head", center, q, (0.012, 0.17, 0.015), M_SCAN)

core_pos = core.matrix_world.translation.copy() if core else Vector((0,0,0))
thin_box("V16_MatCarrier_Alert", "body", core_pos, Quaternion((1,0,0,0)), (0.003,0.003,0.003), M_ALERT)
thin_box("V16_MatCarrier_Attack", "body", core_pos, Quaternion((1,0,0,0)), (0.003,0.003,0.003), M_ATTACK)

root["PredatorRefitVersion"] = "1.6"
root["PredatorStanceAction"] = ACTION_NAME
root["VisualDirection"] = "Low crouched pounce predator; small armored body; low hanging eye; long reach; angular joint covers."
root["WeakPointVisualRule"] = "Dormant matte grey; pale whitish-yellow only after discovery/hit."
root["SignalStateRule"] = "Scanning white; Alert yellow; Attacking red."
root["ArmorBreakRule"] = "Weak-point cover breaks/hides in Unreal and spawns loot pickup."

bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root

print("AFTERFALL Leaper V1.6 Pounce Predator applied.")
print("Action:", ACTION_NAME)
print("Frame 1 shows the new crouched predator stance.")
print("This patch does NOT permanently apply the pose as the armature rest pose.")
