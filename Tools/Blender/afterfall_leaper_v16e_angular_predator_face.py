import bpy
import math
from mathutils import Vector

# AFTERFALL - LEAPER V1.6E ANGULAR PREDATOR FACE
# Blender 5.2+
#
# Fix for the "round face" problem:
# - completely hides the old circular Eye_Lens / Eye_OuterRing / Eye_InnerRing
# - removes prior V16B/C/D face shells
# - builds an angular wedge-shaped armored head around a SMALL recessed sensor
# - keeps only a compact broken circular state-light INSIDE the angular head
# - keeps the Eye weak-point on cover_eye with LEAP_WP_Eye_Grey so current
#   Unreal discovery / armor-break / loot logic remains compatible
#
# Run on Leaper_Standard_Final.blend after the existing weak-point / V1.6 passes.

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

def mat(name, base, metallic=0.0, rough=0.4, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    if not p:
        p = m.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (*base, 1.0)
    p.inputs["Metallic"].default_value = metallic
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

def rigid_skin(o, bone_name):
    if not o or o.type != 'MESH':
        return
    world = o.matrix_world.copy()
    for md in list(o.modifiers):
        if md.type == 'ARMATURE':
            o.modifiers.remove(md)
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

def angular_prism(name, center, forward, side, up, points, depth, offset,
                  material, bone="head", bevel=0.012):
    f = Vector(forward).normalized()
    s = Vector(side).normalized()
    u = Vector(up).normalized()
    front = center + f * (offset + depth * 0.5)
    back = center + f * (offset - depth * 0.5)

    verts = []
    for ps, pu in points:
        verts.append(tuple(front + s * ps + u * pu))
    for ps, pu in points:
        verts.append(tuple(back + s * ps + u * pu))

    n = len(points)
    faces = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n+j, n+i))

    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    setmat(o, material)

    if bevel > 0:
        b = o.modifiers.new("V16E_Bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        try:
            bpy.ops.object.modifier_apply(modifier=b.name)
        except Exception:
            pass
        o.select_set(False)

    rigid_skin(o, bone)
    return o

def disc(name, center, forward, radius, depth, material, bone="head", verts=12):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=radius, depth=depth, location=center
    )
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector(forward).normalized().to_track_quat('Z', 'Y')
    setmat(o, material)
    rigid_skin(o, bone)
    return o

def arc(name, center, forward, side, up, radius, tube, start_deg, end_deg,
        material, bone="head", segments=12):
    f = Vector(forward).normalized()
    s = Vector(side).normalized()
    u = Vector(up).normalized()

    pts = []
    for i in range(segments + 1):
        a = math.radians(start_deg + (end_deg - start_deg) * i / segments)
        pts.append(center + s * math.cos(a) * radius + u * math.sin(a) * radius)

    ring_sides = 6
    verts = []
    for i, p in enumerate(pts):
        prev_p = pts[max(0, i-1)]
        next_p = pts[min(len(pts)-1, i+1)]
        tangent = (next_p - prev_p).normalized()
        n1 = tangent.cross(f)
        if n1.length < 0.001:
            n1 = u.copy()
        n1.normalize()
        n2 = tangent.cross(n1).normalized()
        for j in range(ring_sides):
            t = 2.0 * math.pi * j / ring_sides
            q = p + n1 * math.cos(t) * tube + n2 * math.sin(t) * tube
            verts.append(tuple(q))

    faces = []
    for i in range(len(pts)-1):
        for j in range(ring_sides):
            nj = (j + 1) % ring_sides
            a = i * ring_sides + j
            b = i * ring_sides + nj
            c = (i+1) * ring_sides + nj
            d = (i+1) * ring_sides + j
            faces.append((a,b,c,d))

    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    setmat(o, material)
    rigid_skin(o, bone)
    return o

def carrier(name, location, material):
    bpy.ops.mesh.primitive_cube_add(location=location)
    o = bpy.context.object
    o.name = name
    o.scale = (0.006, 0.006, 0.006)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    setmat(o, material)
    rigid_skin(o, "body")
    o.hide_viewport = True
    o.hide_render = True
    return o

# -------------------------------------------------------------------------
# Cleanup old face experiments
# -------------------------------------------------------------------------
for o in list(bpy.data.objects):
    if o.name.startswith("V16E_"):
        bpy.data.objects.remove(o, do_unlink=True)

for o in bpy.data.objects:
    if o.name.startswith(("V16B_", "V16C_", "V16D_")):
        o.hide_viewport = True
        o.hide_render = True
        try:
            o.hide_set(True)
        except Exception:
            pass

# Hide the old circular face components completely.
# These were the reason the model still read as a round face.
legacy_eye_names = (
    "Eye_Lens",
    "Eye_OuterRing",
    "Eye_InnerRing",
    "WP_Eye_Cover",
)
legacy_eye_objects = [obj(n) for n in legacy_eye_names if obj(n)]

# Use the old eye only as a positional anchor BEFORE hiding it.
eye = obj("Eye_Lens")
body = obj("Core_Body")
if not body:
    raise RuntimeError("Core_Body not found.")

if eye:
    anchor = eye.matrix_world.translation.copy()
    eye_size = max(eye.dimensions)
else:
    # Fallback for reruns after the old eye was already removed/hidden.
    bone = rig.pose.bones.get("weak_eye") or rig.pose.bones.get("head")
    if not bone:
        raise RuntimeError("No Eye_Lens or weak_eye/head bone found for face anchor.")
    anchor = rig.matrix_world @ bone.head
    eye_size = 0.48

body_pos = body.matrix_world.translation.copy()

forward = anchor - body_pos
if forward.length < 0.001:
    forward = Vector((1,0,0))
forward.normalize()

world_up = Vector((0,0,1))
side = world_up.cross(forward)
if side.length < 0.001:
    side = Vector((0,1,0))
side.normalize()
up = forward.cross(side).normalized()

for o in legacy_eye_objects:
    o.hide_viewport = True
    o.hide_render = True
    try:
        o.hide_set(True)
    except Exception:
        pass

# Face size. The sensor is intentionally much smaller than the old round face.
R = max(0.20, eye_size * 0.46)
SENSOR_R = 0.30 * R

M_BLACK = mat("LEAP_FINAL_BlackArmor", (0.004,0.006,0.009), 0.94, 0.22)
M_GRAPH = mat("LEAP_FINAL_GraphiteArmor", (0.022,0.027,0.034), 0.88, 0.28)
M_MECH = mat("LEAP_FINAL_MechanicalDark", (0.008,0.011,0.016), 0.96, 0.18)
M_WP = mat("LEAP_WP_Eye_Grey", (0.095,0.102,0.110), 0.80, 0.31)

M_SCAN = mat("LEAP_SIGNAL_Scan_White", (0.78,0.78,0.72), 0.04, 0.15,
             (1.0,0.92,0.72), 5.0)
M_ALERT = mat("LEAP_SIGNAL_Alert_Yellow", (0.48,0.25,0.02), 0.04, 0.15,
              (1.0,0.42,0.01), 7.0)
M_ATTACK = mat("LEAP_SIGNAL_Attack_Red", (0.30,0.01,0.008), 0.04, 0.14,
               (1.0,0.025,0.012), 9.0)
M_DISC = mat("LEAP_WP_Discovered_PaleYellow", (0.78,0.70,0.45), 0.12, 0.21,
             (1.0,0.84,0.46), 4.0)
M_HIT = mat("LEAP_WP_Hit_WhiteYellow", (0.98,0.92,0.66), 0.06, 0.16,
            (1.0,0.95,0.60), 10.0)

# Bring the new face slightly forward and lower so it hangs under the chest.
face_center = anchor + forward * (0.05*R) - up * (0.10*R)

# -------------------------------------------------------------------------
# ANGULAR OUTER SILHOUETTE - no round head shell
# -------------------------------------------------------------------------
# Top crown / brow shield: wide, tapered, predatory.
angular_prism(
    "V16E_Crown",
    face_center, forward, side, up,
    [(-1.15*R,0.58*R), (-0.60*R,1.25*R), (0.0,1.42*R),
     (0.60*R,1.25*R), (1.15*R,0.58*R),
     (0.82*R,0.30*R), (0.0,0.52*R), (-0.82*R,0.30*R)],
    0.34*R, 0.04*R, M_BLACK, "head", 0.035*R
)

# Side cheek blades create the sloped V-shaped head instead of a circle.
angular_prism(
    "V16E_Cheek_L",
    face_center, forward, side, up,
    [(-1.20*R,0.35*R), (-0.78*R,0.45*R), (-0.60*R,0.05*R),
     (-0.68*R,-0.74*R), (-0.26*R,-1.10*R), (-0.78*R,-1.20*R),
     (-1.28*R,-0.48*R)],
    0.30*R, 0.08*R, M_GRAPH, "head", 0.030*R
)
angular_prism(
    "V16E_Cheek_R",
    face_center, forward, side, up,
    [(1.20*R,0.35*R), (0.78*R,0.45*R), (0.60*R,0.05*R),
     (0.68*R,-0.74*R), (0.26*R,-1.10*R), (0.78*R,-1.20*R),
     (1.28*R,-0.48*R)],
    0.30*R, 0.08*R, M_BLACK, "head", 0.030*R
)

# Center forehead spike / nose keel.
angular_prism(
    "V16E_NoseKeel",
    face_center, forward, side, up,
    [(-0.18*R,0.70*R), (0.18*R,0.70*R), (0.11*R,0.12*R),
     (0.00*R,-0.18*R), (-0.11*R,0.12*R)],
    0.38*R, 0.13*R, M_BLACK, "head", 0.022*R
)

# Lower jaw/chin armor: pointed, not circular.
angular_prism(
    "V16E_Chin",
    face_center, forward, side, up,
    [(-0.72*R,-0.54*R), (-0.40*R,-0.95*R), (0.0,-1.38*R),
     (0.40*R,-0.95*R), (0.72*R,-0.54*R),
     (0.38*R,-0.44*R), (0.0,-0.80*R), (-0.38*R,-0.44*R)],
    0.27*R, 0.10*R, M_GRAPH, "head", 0.028*R
)

# Side fangs.
angular_prism(
    "V16E_Fang_L",
    face_center, forward, side, up,
    [(-0.78*R,-0.88*R), (-0.55*R,-0.92*R),
     (-0.62*R,-1.63*R), (-0.86*R,-1.25*R)],
    0.17*R, 0.10*R, M_BLACK, "head", 0.015*R
)
angular_prism(
    "V16E_Fang_R",
    face_center, forward, side, up,
    [(0.78*R,-0.88*R), (0.55*R,-0.92*R),
     (0.62*R,-1.63*R), (0.86*R,-1.25*R)],
    0.17*R, 0.10*R, M_BLACK, "head", 0.015*R
)

# -------------------------------------------------------------------------
# INTEGRATED EYE WEAK-POINT ARMOR - angular U shape
# -------------------------------------------------------------------------
# This is the lootable breakable eye armor assembly.
angular_prism(
    "V16E_WP_Eye_L",
    face_center, forward, side, up,
    [(-0.72*R,0.10*R), (-0.47*R,0.22*R), (-0.34*R,-0.04*R),
     (-0.38*R,-0.56*R), (-0.12*R,-0.76*R), (-0.42*R,-0.90*R),
     (-0.70*R,-0.52*R)],
    0.19*R, 0.20*R, M_WP, "cover_eye", 0.018*R
)
angular_prism(
    "V16E_WP_Eye_R",
    face_center, forward, side, up,
    [(0.72*R,0.10*R), (0.47*R,0.22*R), (0.34*R,-0.04*R),
     (0.38*R,-0.56*R), (0.12*R,-0.76*R), (0.42*R,-0.90*R),
     (0.70*R,-0.52*R)],
    0.19*R, 0.20*R, M_WP, "cover_eye", 0.018*R
)
angular_prism(
    "V16E_WP_Eye_Bottom",
    face_center, forward, side, up,
    [(-0.30*R,-0.60*R), (0.30*R,-0.60*R), (0.18*R,-0.92*R),
     (0.0,-1.10*R), (-0.18*R,-0.92*R)],
    0.20*R, 0.21*R, M_WP, "cover_eye", 0.018*R
)

# -------------------------------------------------------------------------
# SMALL recessed sensor - only the light itself remains circular
# -------------------------------------------------------------------------
sensor_center = face_center + forward * (0.23*R) - up * (0.08*R)

# Faceted 10-sided aperture so even the optic reads mechanical, not "cute".
disc("V16E_SensorSocket", sensor_center, forward,
     0.42*R, 0.11*R, M_MECH, "head", 10)
disc("V16E_SensorPupil", sensor_center + forward*(0.07*R), forward,
     SENSOR_R, 0.05*R, M_BLACK, "head", 10)

# Compact broken state ring. It is deliberately much smaller than the old face.
state_radius = 0.43 * R
arc("V16E_State_Upper", sensor_center + forward*(0.09*R),
    forward, side, up, state_radius, 0.035*R, 22, 158, M_SCAN, "head", 12)
arc("V16E_State_Left", sensor_center + forward*(0.09*R),
    forward, side, up, state_radius, 0.035*R, 166, 242, M_SCAN, "head", 8)
arc("V16E_State_Right", sensor_center + forward*(0.09*R),
    forward, side, up, state_radius, 0.035*R, -62, 14, M_SCAN, "head", 8)
arc("V16E_State_Bottom", sensor_center + forward*(0.09*R),
    forward, side, up, state_radius, 0.035*R, 252, 288, M_SCAN, "head", 6)

# Narrow slit above the optic adds a more hostile expression.
angular_prism(
    "V16E_UpperSlit",
    face_center + up*(0.39*R), forward, side, up,
    [(-0.38*R,0.02*R), (0.38*R,0.02*R),
     (0.30*R,-0.08*R), (-0.30*R,-0.08*R)],
    0.06*R, 0.24*R, M_SCAN, "head", 0.010*R
)

# Material carriers ensure Unreal imports every state/feedback material slot.
carrier_base = body_pos + Vector((0,0,0.02))
carrier("V16E_Carrier_Alert", carrier_base + Vector((0,0.012,0)), M_ALERT)
carrier("V16E_Carrier_Attack", carrier_base + Vector((0,-0.012,0)), M_ATTACK)
carrier("V16E_Carrier_Discovered", carrier_base + Vector((0,0.024,0)), M_DISC)
carrier("V16E_Carrier_Hit", carrier_base + Vector((0,-0.024,0)), M_HIT)

root["FaceRefitVersion"] = "1.6E"
root["FaceDesign"] = (
    "Angular wedge predator head. Old round face meshes hidden. "
    "Only compact recessed sensor/state ring remains circular."
)
root["EyeWeakPoint"] = (
    "Integrated angular U-shaped armor on cover_eye. Dormant grey -> "
    "pale yellow discovered -> armor break / loot."
)
root["SignalStateRule"] = "Scanning white; Alert yellow; Attacking red."
root["RoundFaceRemoved"] = True

bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root

print("AFTERFALL Leaper V1.6E angular predator face applied.")
print("Old Eye_Lens / Eye_OuterRing / Eye_InnerRing / WP_Eye_Cover are hidden.")
print("The head silhouette is now angular; only the compact sensor light is circular.")
