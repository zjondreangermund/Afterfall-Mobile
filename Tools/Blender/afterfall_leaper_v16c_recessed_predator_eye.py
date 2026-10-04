import bpy, math
from mathutils import Vector, Matrix, Quaternion

# AFTERFALL - LEAPER V1.6C "RECESSED PREDATOR EYE"
# Face-only refinement for Blender 5.2+.
# Keeps the eye/weak-point circle size unchanged.

ROOT_NAME = "LEAPER_ROOT"
RIG_NAME = "ARM_Leaper_Final"

root = bpy.data.objects.get(ROOT_NAME)
rig = bpy.data.objects.get(RIG_NAME)

if not root:
    raise RuntimeError("LEAPER_ROOT not found.")
if not rig or rig.type != 'ARMATURE':
    raise RuntimeError("ARM_Leaper_Final not found.")

scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()

def obj(name):
    return bpy.data.objects.get(name)

def mat(name, base, metal=0.0, rough=0.4, emission=None, strength=0.0):
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

def cleanup():
    for o in list(bpy.data.objects):
        if o.name.startswith("V16C_"):
            bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects:
        if o.name.startswith("V16B_"):
            o.hide_viewport = True
            o.hide_render = True

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
    arm = o.modifiers.new("Leaper_Final_Rig", "ARMATURE")
    arm.object = rig
    o.parent = rig
    o.parent_type = 'OBJECT'
    o.matrix_world = world

def make_box(name, center, quat, scale, material, bone="head", bevel=0.018):
    bpy.ops.mesh.primitive_cube_add(location=center)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = quat
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        b = o.modifiers.new("V16C_Bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
        bpy.context.view_layer.objects.active = o
        try:
            bpy.ops.object.modifier_apply(modifier=b.name)
        except Exception:
            pass
    setmat(o, material)
    rigid_skin(o, bone)
    return o

def make_disc(name, center, forward, radius, depth, material, bone="head"):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=radius, depth=depth, location=center
    )
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = forward.to_track_quat('Z', 'Y')
    setmat(o, material)
    rigid_skin(o, bone)
    return o

cleanup()

eye = obj("Eye_Lens")
cover = obj("WP_Eye_Cover")
body = obj("Core_Body")

if not eye:
    raise RuntimeError("Eye_Lens not found.")
if not body:
    raise RuntimeError("Core_Body not found.")

eye_pos = eye.matrix_world.translation.copy()
body_pos = body.matrix_world.translation.copy()

forward = eye_pos - body_pos
if forward.length < 0.001:
    forward = Vector((1.0, 0.0, 0.0))
forward.normalize()

world_up = Vector((0.0, 0.0, 1.0))
side = world_up.cross(forward)
if side.length < 0.001:
    side = Vector((0.0, 1.0, 0.0))
side.normalize()
up = forward.cross(side).normalized()

basis = Matrix((
    (forward.x, side.x, up.x),
    (forward.y, side.y, up.y),
    (forward.z, side.z, up.z),
))
face_q = basis.to_quaternion()

M_BLACK = mat("LEAP_V16C_BlackArmor", (0.004, 0.006, 0.009), 0.96, 0.20)
M_GUN = mat("LEAP_V16C_Gunmetal", (0.016, 0.021, 0.028), 0.96, 0.21)
M_PUPIL = mat("LEAP_V16C_Pupil", (0.002, 0.003, 0.004), 0.92, 0.14)
M_WP = mat("LEAP_V16_WeakPoint_DormantGrey", (0.105, 0.110, 0.118), 0.80, 0.31)
M_SCAN = mat(
    "LEAP_SIGNAL_Scan_White",
    (0.70, 0.72, 0.69),
    0.03, 0.13,
    (1.0, 0.96, 0.80),
    4.0
)

if cover:
    setmat(cover, M_WP)

for ring_name in ("Eye_OuterRing", "Eye_InnerRing"):
    setmat(obj(ring_name), M_GUN)

if not root.get("V16C_EyeRecessApplied", False):
    recess = -forward * 0.045
    for name in ("Eye_Lens", "WP_Eye_Cover"):
        o = obj(name)
        if o:
            mw = o.matrix_world.copy()
            mw.translation += recess
            o.matrix_world = mw
    root["V16C_EyeRecessApplied"] = True

bpy.context.view_layer.update()
eye_pos = eye.matrix_world.translation.copy()

make_box(
    "V16C_Brow_L",
    eye_pos + forward * 0.025 + side * 0.085 + up * 0.165,
    Quaternion(forward, math.radians(-8.0)) @ face_q,
    (0.070, 0.185, 0.055), M_BLACK, "head", 0.020
)
make_box(
    "V16C_Brow_R",
    eye_pos + forward * 0.030 - side * 0.070 + up * 0.150,
    Quaternion(forward, math.radians(13.0)) @ face_q,
    (0.075, 0.210, 0.060), M_BLACK, "head", 0.020
)
make_box(
    "V16C_Cheek_L",
    eye_pos + forward * 0.005 + side * 0.235 - up * 0.015,
    Quaternion(forward, math.radians(19.0)) @ face_q,
    (0.085, 0.070, 0.175), M_GUN, "head", 0.018
)
make_box(
    "V16C_Cheek_R",
    eye_pos + forward * 0.010 - side * 0.215 - up * 0.030,
    Quaternion(forward, math.radians(-27.0)) @ face_q,
    (0.080, 0.060, 0.150), M_BLACK, "head", 0.018
)
make_box(
    "V16C_LowerGuard",
    eye_pos - up * 0.205,
    face_q,
    (0.070, 0.180, 0.032), M_BLACK, "head", 0.014
)
make_box(
    "V16C_LowerBlade_L",
    eye_pos + forward * 0.015 + side * 0.145 - up * 0.145,
    Quaternion(forward, math.radians(31.0)) @ face_q,
    (0.065, 0.028, 0.095), M_GUN, "head", 0.010
)
make_box(
    "V16C_LowerBlade_R",
    eye_pos + forward * 0.010 - side * 0.130 - up * 0.160,
    Quaternion(forward, math.radians(-24.0)) @ face_q,
    (0.058, 0.026, 0.082), M_BLACK, "head", 0.010
)

make_disc(
    "V16C_Pupil",
    eye_pos + forward * 0.022,
    forward,
    0.070, 0.018, M_PUPIL, "head"
)

make_box(
    "V16C_ScanSlit",
    eye_pos + forward * 0.040 + up * 0.115,
    face_q,
    (0.014, 0.095, 0.010), M_SCAN, "head", 0.005
)

root["FaceRefitVersion"] = "1.6C"
root["FaceDesign"] = (
    "Eye circle preserved; optic recessed into skull with asymmetric "
    "predator brow/cheek shroud, dark pupil and tiny state slit."
)
root["WeakPointVisualRule"] = "Dormant matte grey; on hit/discovery pale whitish-yellow."
root["SignalStateRule"] = "Scanning white; Alert yellow; Attacking red."
root["ArmorBreakRule"] = "Weak-point armor detaches in Unreal and can spawn loot."

bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
eye.select_set(True)
bpy.context.view_layer.objects.active = eye

print("AFTERFALL Leaper V1.6C face refinement applied.")
print("Circle size preserved; only the face housing changed.")
print("Body and legs were not rescaled.")
