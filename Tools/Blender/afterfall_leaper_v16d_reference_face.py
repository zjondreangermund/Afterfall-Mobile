import bpy
import math
from mathutils import Vector

# AFTERFALL - LEAPER V1.6D REFERENCE FACE
# Blender 5.2+
#
# Rebuilds ONLY the Leaper face to match the approved concept:
# - low hanging circular sensor/eye
# - angular black armored brow and cheek cage
# - broken circular state-light ring around the eye
# - integrated U-shaped eye weak-point armor (not a loose ring)
# - dormant weak point = graphite/grey
# - discovered weak point = pale yellow (runtime material swap)
# - scanning = white, alert = yellow, attacking = red
# - eye armor uses the existing cover_eye bone / LEAP_WP_Eye_Grey material
#   so the current Unreal weak-point destruction + loot logic still works
#
# Run after the V1.3 weak-point patch / V1.6 predator pass on
# Leaper_Standard_Final.blend.

ROOT_NAME = "LEAPER_ROOT"
RIG_NAME = "ARM_Leaper_Final"

root = bpy.data.objects.get(ROOT_NAME)
rig = bpy.data.objects.get(RIG_NAME)

if not root:
    raise RuntimeError("LEAPER_ROOT not found.")
if not rig or rig.type != 'ARMATURE':
    raise RuntimeError("ARM_Leaper_Final armature not found.")

scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()

def obj(name):
    return bpy.data.objects.get(name)

def make_mat(name, base, metallic=0.0, rough=0.45, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        bsdf = m.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 0.0
    if emission is not None:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*base, 1.0)
    return m

def set_mat(o, m):
    if not o or o.type != 'MESH':
        return
    o.data.materials.clear()
    o.data.materials.append(m)
    o.color = m.diffuse_color

def cleanup():
    for o in list(bpy.data.objects):
        if o.name.startswith("V16D_"):
            bpy.data.objects.remove(o, do_unlink=True)

    for o in bpy.data.objects:
        if o.name.startswith(("V16B_", "V16C_")):
            o.hide_viewport = True
            o.hide_render = True

    old_eye_cover = obj("WP_Eye_Cover")
    if old_eye_cover:
        old_eye_cover.hide_viewport = True
        old_eye_cover.hide_render = True

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
    arm.use_deform_preserve_volume = False

    o.parent = rig
    o.parent_type = 'OBJECT'
    o.matrix_world = world

def make_prism(name, center, forward, side, up, points_su, depth, forward_offset,
               material, bone_name="head", bevel=0.012):
    f = Vector(forward).normalized()
    s = Vector(side).normalized()
    u = Vector(up).normalized()

    front = center + f * (forward_offset + depth * 0.5)
    back = center + f * (forward_offset - depth * 0.5)

    verts = []
    for p_s, p_u in points_su:
        verts.append(tuple(front + s * p_s + u * p_u))
    for p_s, p_u in points_su:
        verts.append(tuple(back + s * p_s + u * p_u))

    n = len(points_su)
    faces = [tuple(range(n)), tuple(range(2*n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))

    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    set_mat(o, material)

    if bevel > 0:
        b = o.modifiers.new("V16D_Bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        try:
            bpy.ops.object.modifier_apply(modifier=b.name)
        except Exception:
            pass
        o.select_set(False)

    rigid_skin(o, bone_name)
    return o

def make_disc(name, center, forward, radius, depth, material, bone_name="head", verts=32):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts,
        radius=radius,
        depth=depth,
        location=center
    )
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector(forward).normalized().to_track_quat('Z', 'Y')
    set_mat(o, material)
    rigid_skin(o, bone_name)
    return o

def make_arc(name, center, forward, side, up, radius, tube_radius,
             start_deg, end_deg, material, bone_name="head", segments=20):
    f = Vector(forward).normalized()
    s = Vector(side).normalized()
    u = Vector(up).normalized()

    pts = []
    for i in range(segments + 1):
        t = math.radians(start_deg + (end_deg - start_deg) * i / segments)
        pts.append(center + s * (math.cos(t) * radius) + u * (math.sin(t) * radius))

    verts = []
    rings = 8
    for p_i, p in enumerate(pts):
        tangent = (pts[min(p_i + 1, len(pts)-1)] - pts[max(p_i - 1, 0)]).normalized()
        n1 = tangent.cross(f)
        if n1.length < 0.001:
            n1 = u.copy()
        n1.normalize()
        n2 = tangent.cross(n1).normalized()

        for j in range(rings):
            a = 2.0 * math.pi * j / rings
            q = p + n1 * (math.cos(a) * tube_radius) + n2 * (math.sin(a) * tube_radius)
            verts.append(tuple(q))

    faces = []
    for i in range(len(pts) - 1):
        for j in range(rings):
            nj = (j + 1) % rings
            a = i * rings + j
            b = i * rings + nj
            c = (i + 1) * rings + nj
            d = (i + 1) * rings + j
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    set_mat(o, material)
    rigid_skin(o, bone_name)
    return o

def add_tiny_carrier(name, location, material):
    if obj(name):
        return obj(name)
    bpy.ops.mesh.primitive_cube_add(location=location)
    o = bpy.context.object
    o.name = name
    o.scale = (0.006, 0.006, 0.006)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    set_mat(o, material)
    rigid_skin(o, "body")
    return o

cleanup()

eye = obj("Eye_Lens")
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

eye_size = max(eye.dimensions)
R = max(0.22, eye_size * 0.52)

M_BLACK = make_mat("LEAP_FINAL_BlackArmor", (0.006, 0.008, 0.011), 0.92, 0.22)
M_GRAPHITE = make_mat("LEAP_FINAL_GraphiteArmor", (0.025, 0.030, 0.038), 0.84, 0.27)
M_MECH = make_mat("LEAP_FINAL_MechanicalDark", (0.010, 0.013, 0.018), 0.95, 0.19)
M_EYE_GREY = make_mat("LEAP_WP_Eye_Grey", (0.10, 0.11, 0.12), 0.78, 0.30)

M_SCAN = make_mat("LEAP_SIGNAL_Scan_White", (0.80, 0.78, 0.68), 0.05, 0.16, (1.00, 0.91, 0.72), 5.0)
M_ALERT = make_mat("LEAP_SIGNAL_Alert_Yellow", (0.55, 0.31, 0.03), 0.04, 0.16, (1.00, 0.47, 0.02), 7.0)
M_ATTACK = make_mat("LEAP_SIGNAL_Attack_Red", (0.34, 0.015, 0.01), 0.04, 0.15, (1.00, 0.035, 0.015), 9.0)
M_DISCOVERED = make_mat("LEAP_WP_Discovered_PaleYellow", (0.76, 0.68, 0.40), 0.12, 0.22, (1.00, 0.82, 0.42), 4.0)
M_HIT = make_mat("LEAP_WP_Hit_WhiteYellow", (0.98, 0.91, 0.62), 0.06, 0.16, (1.00, 0.94, 0.58), 10.0)

set_mat(eye, M_MECH)
for ring_name in ("Eye_OuterRing", "Eye_InnerRing"):
    set_mat(obj(ring_name), M_BLACK)

if not root.get("V16D_ReferenceEyeRecess", False):
    for name in ("Eye_Lens", "Eye_OuterRing", "Eye_InnerRing"):
        o = obj(name)
        if o:
            mw = o.matrix_world.copy()
            mw.translation -= forward * (R * 0.10)
            o.matrix_world = mw
    root["V16D_ReferenceEyeRecess"] = True
    bpy.context.view_layer.update()
    eye_pos = eye.matrix_world.translation.copy()

make_prism("V16D_Brow_L", eye_pos, forward, side, up,
    [(-1.15*R, 0.70*R), (-0.55*R, 1.34*R), (-0.08*R, 1.02*R),
     (-0.18*R, 0.46*R), (-0.88*R, 0.34*R)],
    0.26*R, 0.09*R, M_BLACK, "head", 0.035*R)

make_prism("V16D_Brow_R", eye_pos, forward, side, up,
    [(1.12*R, 0.73*R), (0.52*R, 1.30*R), (0.05*R, 1.01*R),
     (0.17*R, 0.44*R), (0.86*R, 0.31*R)],
    0.28*R, 0.10*R, M_GRAPHITE, "head", 0.035*R)

make_prism("V16D_CenterKeel", eye_pos, forward, side, up,
    [(-0.13*R, 0.83*R), (0.10*R, 0.84*R),
     (0.16*R, 0.36*R), (0.00*R, 0.12*R), (-0.17*R, 0.35*R)],
    0.31*R, 0.12*R, M_BLACK, "head", 0.026*R)

make_prism("V16D_JawFrame_L", eye_pos, forward, side, up,
    [(-1.12*R, 0.30*R), (-0.76*R, 0.53*R), (-0.58*R, 0.12*R),
     (-0.63*R, -0.65*R), (-0.92*R, -1.06*R), (-1.18*R, -0.70*R)],
    0.26*R, 0.08*R, M_BLACK, "head", 0.030*R)

make_prism("V16D_JawFrame_R", eye_pos, forward, side, up,
    [(1.08*R, 0.34*R), (0.73*R, 0.50*R), (0.56*R, 0.10*R),
     (0.61*R, -0.60*R), (0.86*R, -1.00*R), (1.13*R, -0.66*R)],
    0.25*R, 0.08*R, M_GRAPHITE, "head", 0.030*R)

make_prism("V16D_WP_Eye_Left", eye_pos, forward, side, up,
    [(-1.00*R, 0.02*R), (-0.72*R, 0.20*R), (-0.55*R, -0.08*R),
     (-0.58*R, -0.68*R), (-0.33*R, -0.92*R), (-0.66*R, -1.04*R),
     (-0.98*R, -0.70*R)],
    0.20*R, 0.17*R, M_EYE_GREY, "cover_eye", 0.022*R)

make_prism("V16D_WP_Eye_Right", eye_pos, forward, side, up,
    [(0.98*R, 0.03*R), (0.71*R, 0.18*R), (0.54*R, -0.10*R),
     (0.58*R, -0.65*R), (0.31*R, -0.91*R), (0.63*R, -1.02*R),
     (0.96*R, -0.67*R)],
    0.20*R, 0.17*R, M_EYE_GREY, "cover_eye", 0.022*R)

make_prism("V16D_WP_Eye_Chin", eye_pos, forward, side, up,
    [(-0.34*R, -0.78*R), (0.34*R, -0.78*R),
     (0.19*R, -1.20*R), (0.00*R, -1.42*R), (-0.20*R, -1.18*R)],
    0.21*R, 0.17*R, M_EYE_GREY, "cover_eye", 0.022*R)

make_disc("V16D_EyeAperture", eye_pos + forward * (0.17*R), forward,
          0.36*R, 0.08*R, M_MECH, "head", 32)
make_disc("V16D_EyePupil", eye_pos + forward * (0.22*R), forward,
          0.12*R, 0.05*R, M_BLACK, "head", 24)

state_center = eye_pos + forward * (0.25*R)
make_arc("V16D_StateRing_Upper", state_center, forward, side, up,
         0.54*R, 0.055*R, 18, 162, M_SCAN, "head", 20)
make_arc("V16D_StateRing_Left", state_center, forward, side, up,
         0.54*R, 0.055*R, 166, 252, M_SCAN, "head", 12)
make_arc("V16D_StateRing_Right", state_center, forward, side, up,
         0.54*R, 0.055*R, -72, 14, M_SCAN, "head", 12)
make_arc("V16D_StateRing_Lower", state_center, forward, side, up,
         0.54*R, 0.055*R, 258, 282, M_SCAN, "head", 8)

make_prism("V16D_ChinSpike_L", eye_pos, forward, side, up,
    [(-0.37*R, -1.03*R), (-0.16*R, -1.06*R),
     (-0.22*R, -1.58*R), (-0.42*R, -1.32*R)],
    0.15*R, 0.07*R, M_BLACK, "head", 0.018*R)

make_prism("V16D_ChinSpike_R", eye_pos, forward, side, up,
    [(0.36*R, -1.02*R), (0.15*R, -1.07*R),
     (0.21*R, -1.55*R), (0.40*R, -1.30*R)],
    0.15*R, 0.07*R, M_GRAPHITE, "head", 0.018*R)

carrier_base = body_pos + Vector((0.0, 0.0, 0.02))
for name, offset, material in (
    ("V16D_MatCarrier_Alert", Vector((0.0, 0.012, 0.0)), M_ALERT),
    ("V16D_MatCarrier_Attack", Vector((0.0, -0.012, 0.0)), M_ATTACK),
    ("V16D_MatCarrier_Discovered", Vector((0.0, 0.024, 0.0)), M_DISCOVERED),
    ("V16D_MatCarrier_Hit", Vector((0.0, -0.024, 0.0)), M_HIT),
):
    c = add_tiny_carrier(name, carrier_base + offset, material)
    c.hide_viewport = True
    c.hide_render = True

root["FaceRefitVersion"] = "1.6D"
root["ApprovedFaceDirection"] = (
    "Reference concept: low hanging circular sensor under sharp black armor, "
    "broken state-light ring, integrated U-shaped breakable weak-point armor."
)
root["EyeStateLight"] = "Scanning white; Alert yellow; Attacking red"
root["EyeWeakPoint"] = (
    "Integrated V16D_WP_Eye_Left/Right/Chin pieces use cover_eye and "
    "LEAP_WP_Eye_Grey. Discovered pale yellow, then breaks off as loot."
)
root["ReferenceFaceLocked"] = True

bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
eye.select_set(True)
bpy.context.view_layer.objects.active = eye

print("AFTERFALL Leaper V1.6D approved reference face applied.")
print("State ring: white scanning -> yellow alert -> red attacking.")
print("Eye weak point is now integrated U-shaped armor, not a loose ring.")
print("Existing Unreal weak-point bones/material names remain compatible.")
