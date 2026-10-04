import bpy
import math
from mathutils import Vector

# AFTERFALL - LEAPER V1.6F INTEGRATED PREDATOR FACE
# Blender 5.2+
#
# This pass fixes the V1.6E "hanging box/cage" look:
# - keeps the circular sensor size prominent (the circle itself was fine)
# - removes the flat forehead slab
# - wraps the sensor in angular armor instead of putting armor in front of it
# - pulls the face closer into the thorax
# - uses split brow plates, cheek wedges, chin armor and a rear neck bridge
# - only the SENSOR is circular; the HEAD SILHOUETTE is angular
# - keeps weak-point materials / cover_eye bone compatible with Unreal logic
#
# Run on Leaper_Standard_Final.blend after prior V1.6 patches.

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

def make_mat(name, base, metallic=0.0, rough=0.4, emission=None, strength=0.0):
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

def set_mat(o, m):
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

def prism(name, center, forward, side, up, points_su, depth, offset,
          material, bone="head", bevel=0.012):
    f = Vector(forward).normalized()
    s = Vector(side).normalized()
    u = Vector(up).normalized()

    front = center + f * (offset + depth * 0.5)
    back  = center + f * (offset - depth * 0.5)

    verts = []
    for ps, pu in points_su:
        verts.append(tuple(front + s*ps + u*pu))
    for ps, pu in points_su:
        verts.append(tuple(back + s*ps + u*pu))

    n = len(points_su)
    faces = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n+j, n+i))

    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    set_mat(o, material)

    if bevel > 0:
        b = o.modifiers.new("V16F_Bevel", "BEVEL")
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

def disc(name, center, forward, radius, depth, material, bone="head", verts=14):
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
    rigid_skin(o, bone)
    return o

def arc(name, center, forward, side, up, radius, tube_radius,
        start_deg, end_deg, material, bone="head", segments=14):
    f = Vector(forward).normalized()
    s = Vector(side).normalized()
    u = Vector(up).normalized()

    pts = []
    for i in range(segments + 1):
        a = math.radians(start_deg + (end_deg-start_deg) * i / segments)
        pts.append(center + s*(math.cos(a)*radius) + u*(math.sin(a)*radius))

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
            a = 2.0*math.pi*j/ring_sides
            q = p + n1*math.cos(a)*tube_radius + n2*math.sin(a)*tube_radius
            verts.append(tuple(q))

    faces = []
    for i in range(len(pts)-1):
        for j in range(ring_sides):
            nj = (j+1) % ring_sides
            a = i*ring_sides + j
            b = i*ring_sides + nj
            c = (i+1)*ring_sides + nj
            d = (i+1)*ring_sides + j
            faces.append((a,b,c,d))

    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    set_mat(o, material)
    rigid_skin(o, bone)
    return o

def tiny_carrier(name, location, material):
    bpy.ops.mesh.primitive_cube_add(location=location)
    o = bpy.context.object
    o.name = name
    o.scale = (0.006,0.006,0.006)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    set_mat(o, material)
    rigid_skin(o, "body")
    o.hide_viewport = True
    o.hide_render = True
    return o

# -------------------------------------------------------------------------
# CLEANUP
# -------------------------------------------------------------------------
for o in list(bpy.data.objects):
    if o.name.startswith("V16F_"):
        bpy.data.objects.remove(o, do_unlink=True)

for o in bpy.data.objects:
    if o.name.startswith(("V16B_","V16C_","V16D_","V16E_")):
        o.hide_viewport = True
        o.hide_render = True
        try:
            o.hide_set(True)
        except Exception:
            pass

legacy_names = ("Eye_Lens","Eye_OuterRing","Eye_InnerRing","WP_Eye_Cover")
legacy = [obj(n) for n in legacy_names if obj(n)]

eye = obj("Eye_Lens")
body = obj("Core_Body")
if not body:
    raise RuntimeError("Core_Body not found.")

if eye:
    anchor = eye.matrix_world.translation.copy()
    eye_size = max(eye.dimensions)
else:
    pb = rig.pose.bones.get("weak_eye") or rig.pose.bones.get("head")
    if not pb:
        raise RuntimeError("No eye anchor available.")
    anchor = rig.matrix_world @ pb.head
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

for o in legacy:
    o.hide_viewport = True
    o.hide_render = True
    try:
        o.hide_set(True)
    except Exception:
        pass

# Keep roughly the original circle size; user approved the circle.
R = max(0.23, eye_size * 0.53)

M_BLACK = make_mat("LEAP_FINAL_BlackArmor", (0.004,0.006,0.009), 0.94, 0.22)
M_GRAPH = make_mat("LEAP_FINAL_GraphiteArmor", (0.020,0.026,0.034), 0.88, 0.27)
M_MECH = make_mat("LEAP_FINAL_MechanicalDark", (0.008,0.011,0.016), 0.96, 0.18)
M_WP = make_mat("LEAP_WP_Eye_Grey", (0.095,0.102,0.110), 0.80, 0.31)

M_SCAN = make_mat("LEAP_SIGNAL_Scan_White", (0.80,0.78,0.68), 0.04, 0.15,
                  (1.0,0.92,0.72), 5.0)
M_ALERT = make_mat("LEAP_SIGNAL_Alert_Yellow", (0.50,0.26,0.02), 0.04, 0.15,
                   (1.0,0.44,0.01), 7.0)
M_ATTACK = make_mat("LEAP_SIGNAL_Attack_Red", (0.30,0.01,0.008), 0.04, 0.14,
                    (1.0,0.025,0.012), 9.0)
M_DISC = make_mat("LEAP_WP_Discovered_PaleYellow", (0.78,0.70,0.45), 0.12, 0.21,
                  (1.0,0.84,0.46), 4.0)
M_HIT = make_mat("LEAP_WP_Hit_WhiteYellow", (0.98,0.92,0.66), 0.06, 0.16,
                 (1.0,0.95,0.60), 10.0)

# Pull the face upward/back toward the chassis so it no longer looks detached.
face = anchor - forward*(0.02*R) + up*(0.05*R)

# -------------------------------------------------------------------------
# REAR NECK BRIDGE - makes head feel structurally attached to thorax
# -------------------------------------------------------------------------
prism(
    "V16F_NeckBridge",
    face + up*(0.44*R),
    forward, side, up,
    [(-0.54*R,0.22*R),(0.54*R,0.22*R),(0.42*R,0.62*R),
     (0.0,0.78*R),(-0.42*R,0.62*R)],
    0.82*R, -0.22*R, M_BLACK, "head", 0.030*R
)

# -------------------------------------------------------------------------
# SPLIT BROWS - sloped armor, no flat forehead slab
# -------------------------------------------------------------------------
prism(
    "V16F_Brow_L",
    face, forward, side, up,
    [(-1.12*R,0.48*R),(-0.52*R,1.10*R),(-0.08*R,0.92*R),
     (-0.12*R,0.44*R),(-0.70*R,0.28*R)],
    0.34*R, 0.10*R, M_BLACK, "head", 0.030*R
)
prism(
    "V16F_Brow_R",
    face, forward, side, up,
    [(1.12*R,0.48*R),(0.52*R,1.10*R),(0.08*R,0.92*R),
     (0.12*R,0.44*R),(0.70*R,0.28*R)],
    0.34*R, 0.10*R, M_GRAPH, "head", 0.030*R
)

# Central top wedge gives the face the pointed concept-art crown.
prism(
    "V16F_CenterForehead",
    face, forward, side, up,
    [(-0.18*R,0.98*R),(0.18*R,0.98*R),(0.13*R,0.52*R),
     (0.0,0.25*R),(-0.13*R,0.52*R)],
    0.38*R, 0.14*R, M_BLACK, "head", 0.020*R
)

# -------------------------------------------------------------------------
# CHEEKS - wrap around sensor without making a circular outer silhouette
# -------------------------------------------------------------------------
prism(
    "V16F_Cheek_L",
    face, forward, side, up,
    [(-1.16*R,0.18*R),(-0.76*R,0.40*R),(-0.53*R,0.10*R),
     (-0.52*R,-0.54*R),(-0.26*R,-0.84*R),(-0.68*R,-1.08*R),
     (-1.12*R,-0.62*R)],
    0.32*R, 0.11*R, M_GRAPH, "head", 0.026*R
)
prism(
    "V16F_Cheek_R",
    face, forward, side, up,
    [(1.16*R,0.18*R),(0.76*R,0.40*R),(0.53*R,0.10*R),
     (0.52*R,-0.54*R),(0.26*R,-0.84*R),(0.68*R,-1.08*R),
     (1.12*R,-0.62*R)],
    0.32*R, 0.11*R, M_BLACK, "head", 0.026*R
)

# Pointed lower jaw. Compact and tucked in, not dangling.
prism(
    "V16F_Chin",
    face, forward, side, up,
    [(-0.48*R,-0.68*R),(0.48*R,-0.68*R),(0.30*R,-1.00*R),
     (0.0,-1.28*R),(-0.30*R,-1.00*R)],
    0.28*R, 0.12*R, M_BLACK, "head", 0.025*R
)

# Short lower fangs.
prism(
    "V16F_Fang_L",
    face, forward, side, up,
    [(-0.72*R,-0.80*R),(-0.52*R,-0.82*R),
     (-0.58*R,-1.36*R),(-0.78*R,-1.08*R)],
    0.15*R, 0.13*R, M_GRAPH, "head", 0.012*R
)
prism(
    "V16F_Fang_R",
    face, forward, side, up,
    [(0.72*R,-0.80*R),(0.52*R,-0.82*R),
     (0.58*R,-1.36*R),(0.78*R,-1.08*R)],
    0.15*R, 0.13*R, M_GRAPH, "head", 0.012*R
)

# -------------------------------------------------------------------------
# SENSOR - prominent circle as requested, but recessed in angular armor
# -------------------------------------------------------------------------
sensor_center = face + forward*(0.24*R) - up*(0.06*R)

disc("V16F_SensorSocket", sensor_center, forward,
     0.48*R, 0.12*R, M_MECH, "head", 14)
disc("V16F_SensorCore", sensor_center + forward*(0.075*R), forward,
     0.24*R, 0.05*R, M_BLACK, "head", 14)

# Broken state ring, similar visual size to the approved circle.
state_radius = 0.54*R
for name, a0, a1, seg in (
    ("V16F_State_Upper", 20, 160, 14),
    ("V16F_State_Left", 168, 246, 8),
    ("V16F_State_Right", -66, 12, 8),
    ("V16F_State_Bottom", 254, 286, 6),
):
    arc(name, sensor_center + forward*(0.11*R),
        forward, side, up, state_radius, 0.042*R,
        a0, a1, M_SCAN, "head", seg)

# -------------------------------------------------------------------------
# BREAKABLE WEAK-POINT ARMOR - integrated side pieces + lower lock
# -------------------------------------------------------------------------
prism(
    "V16F_WP_Eye_L",
    face, forward, side, up,
    [(-0.74*R,0.05*R),(-0.54*R,0.18*R),(-0.42*R,-0.06*R),
     (-0.44*R,-0.52*R),(-0.20*R,-0.72*R),(-0.44*R,-0.86*R),
     (-0.70*R,-0.50*R)],
    0.20*R, 0.21*R, M_WP, "cover_eye", 0.016*R
)
prism(
    "V16F_WP_Eye_R",
    face, forward, side, up,
    [(0.74*R,0.05*R),(0.54*R,0.18*R),(0.42*R,-0.06*R),
     (0.44*R,-0.52*R),(0.20*R,-0.72*R),(0.44*R,-0.86*R),
     (0.70*R,-0.50*R)],
    0.20*R, 0.21*R, M_WP, "cover_eye", 0.016*R
)
prism(
    "V16F_WP_Eye_Lower",
    face, forward, side, up,
    [(-0.28*R,-0.62*R),(0.28*R,-0.62*R),
     (0.18*R,-0.86*R),(0.0,-1.00*R),(-0.18*R,-0.86*R)],
    0.19*R, 0.22*R, M_WP, "cover_eye", 0.016*R
)

# Thin hostile slit above eye.
prism(
    "V16F_ScanSlit",
    face + up*(0.42*R), forward, side, up,
    [(-0.34*R,0.025*R),(0.34*R,0.025*R),
     (0.27*R,-0.07*R),(-0.27*R,-0.07*R)],
    0.055*R, 0.25*R, M_SCAN, "head", 0.008*R
)

# Hidden material carriers for Unreal state swaps.
carrier_base = body_pos + Vector((0,0,0.02))
tiny_carrier("V16F_Carrier_Alert", carrier_base + Vector((0,0.012,0)), M_ALERT)
tiny_carrier("V16F_Carrier_Attack", carrier_base + Vector((0,-0.012,0)), M_ATTACK)
tiny_carrier("V16F_Carrier_Discovered", carrier_base + Vector((0,0.024,0)), M_DISC)
tiny_carrier("V16F_Carrier_Hit", carrier_base + Vector((0,-0.024,0)), M_HIT)

root["FaceRefitVersion"] = "1.6F"
root["FaceDesign"] = (
    "Integrated angular predator face. Split brows + cheek wedges + pointed chin; "
    "sensor remains prominent but only the sensor is circular."
)
root["FaceCircleRule"] = "Keep sensor circle size; never use a circular outer head shell."
root["EyeWeakPoint"] = (
    "Integrated V16F_WP_Eye_L/R/Lower on cover_eye; dormant grey -> "
    "pale yellow discovered -> breakable loot."
)
root["SignalStateRule"] = "Scanning white; Alert yellow; Attacking red."

bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root

print("AFTERFALL Leaper V1.6F integrated predator face applied.")
print("Circle size preserved as a sensor; surrounding head is angular and body-integrated.")
