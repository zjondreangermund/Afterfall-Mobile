import bpy, math
from mathutils import Vector, Matrix, Quaternion

# AFTERFALL - LEAPER V1.6B FACE REFIT
# Keeps the circular eye/weak-point size unchanged and redesigns only the face.
# Safe to run on the current partially-applied V1.6 scene.
# Blender 5.2+

ROOT_NAME = "LEAPER_ROOT"
RIG_NAME = "ARM_Leaper_Final"

root = bpy.data.objects.get(ROOT_NAME)
rig = bpy.data.objects.get(RIG_NAME)

if not root:
    raise RuntimeError("LEAPER_ROOT not found.")
if not rig or rig.type != 'ARMATURE':
    raise RuntimeError("ARM_Leaper_Final not found.")

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
        if o.name.startswith("V16B_"):
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
    arm = o.modifiers.new("Leaper_Final_Rig", "ARMATURE")
    arm.object = rig
    o.parent = rig
    o.parent_type = 'OBJECT'
    o.matrix_world = world

def make_box(name, center, quat, scale, material, bone="head", bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(location=center)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = quat
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b = o.modifiers.new("V16B_Bevel", "BEVEL")
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

cleanup()

old_slit = obj("V16_SensorSlit")
if old_slit:
    old_slit.hide_viewport = True
    old_slit.hide_render = True

eye = obj("Eye_Lens") or obj("WP_Eye_Cover")
body = obj("Core_Body")

if not eye:
    raise RuntimeError("Eye_Lens / WP_Eye_Cover not found.")
if not body:
    raise RuntimeError("Core_Body not found.")

eye_scale_before = eye.scale.copy()
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

M_BLACK = mat("LEAP_V16B_Face_Black", (0.006, 0.007, 0.010), 0.95, 0.20)
M_GUN = mat("LEAP_V16B_Face_Gunmetal", (0.018, 0.022, 0.030), 0.95, 0.22)
M_WP = mat("LEAP_V16_WeakPoint_DormantGrey", (0.105, 0.110, 0.118), 0.80, 0.31)
M_SCAN = mat("LEAP_SIGNAL_Scan_White", (0.72, 0.74, 0.70), 0.02, 0.13, (1.0, 0.94, 0.75), 4.5)

setmat(obj("WP_Eye_Cover"), M_WP)

depth_back = -0.075

make_box(
    "V16B_Brow",
    eye_pos + up * 0.215 + forward * depth_back,
    face_q,
    (0.105, 0.285, 0.060),
    M_BLACK,
    "head",
    0.025,
)

for sign, label in ((-1, "L"), (1, "R")):
    center = eye_pos + side * (0.235 * sign) + up * 0.010 + forward * (depth_back - 0.015)
    q = Quaternion(forward, math.radians(20.0 * -sign)) @ face_q
    make_box(
        f"V16B_Cheek_{label}",
        center,
        q,
        (0.105, 0.070, 0.175),
        M_GUN,
        "head",
        0.020,
    )

make_box(
    "V16B_Chin",
    eye_pos - up * 0.205 + forward * (depth_back - 0.010),
    face_q,
    (0.095, 0.205, 0.040),
    M_BLACK,
    "head",
    0.018,
)

make_box(
    "V16B_ScanSlit",
    eye_pos + up * 0.145 + forward * 0.030,
    face_q,
    (0.020, 0.115, 0.014),
    M_SCAN,
    "head",
    0.006,
)

for sign, label in ((-1, "L"), (1, "R")):
    center = eye_pos + side * (0.155 * sign) - up * 0.125 + forward * (depth_back - 0.005)
    q = Quaternion(forward, math.radians(28.0 * sign)) @ face_q
    make_box(
        f"V16B_FaceBlade_{label}",
        center,
        q,
        (0.080, 0.035, 0.115),
        M_BLACK,
        "head",
        0.012,
    )

eye.scale = eye_scale_before
root["FaceRefitVersion"] = "1.6B"
root["FaceDesign"] = "Circular optic size preserved; recessed inside low angular predator brow, cheeks and chin."

bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
eye.select_set(True)
bpy.context.view_layer.objects.active = eye

print("AFTERFALL Leaper V1.6B face refit applied.")
print("Eye/weak-point circle size preserved.")
print("Only the face shroud was redesigned; body/legs were not rescaled.")
