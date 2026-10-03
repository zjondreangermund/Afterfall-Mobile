import bpy
import math
from mathutils import Vector

# AFTERFALL - LEAPER V1.3 BREAKABLE WEAK-POINT PATCH
# Run on top of Leaper_Standard_Final.blend / ARM_Leaper_Final.
# Adds integrated grey arc covers, discovery/hit materials, and cover bones.

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

def world_pos(name, fallback=(0,0,0)):
    o = obj(name)
    return o.matrix_world.translation.copy() if o else Vector(fallback)

def make_mat(name, base, metallic=0.0, rough=0.45, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    else:
        bsdf.inputs["Emission Strength"].default_value = 0.0
    m.diffuse_color = (*base, 1.0)
    return m

def set_mat(o, m):
    if not o or o.type != 'MESH':
        return
    o.data.materials.clear()
    o.data.materials.append(m)
    o.color = m.diffuse_color

def cleanup_v13():
    for o in list(bpy.data.objects):
        if o.name.startswith("WPV13_") or o.name.startswith("WP_"):
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
    arm.use_deform_preserve_volume = False
    o.parent = rig
    o.parent_type = 'OBJECT'
    o.matrix_world = world

def add_tiny_carrier(name, location, material):
    bpy.ops.mesh.primitive_cube_add(location=location)
    o = bpy.context.object
    o.name = name
    o.scale = (0.008,0.008,0.008)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    set_mat(o, material)
    rigid_skin(o, "body")
    return o

def create_arc_plate(name, center, axis, inner_radius, outer_radius, thickness,
                     start_deg, end_deg, material, segments=18):
    verts = []
    faces = []
    for i in range(segments + 1):
        t = math.radians(start_deg + (end_deg-start_deg)*i/segments)
        c, s = math.cos(t), math.sin(t)
        verts.extend([
            (inner_radius*c,inner_radius*s,-thickness/2),
            (inner_radius*c,inner_radius*s, thickness/2),
            (outer_radius*c,outer_radius*s,-thickness/2),
            (outer_radius*c,outer_radius*s, thickness/2),
        ])
    for i in range(segments):
        a, b = i*4, (i+1)*4
        faces += [
            (a+1,b+1,b+3,a+3),
            (a+0,a+2,b+2,b+0),
            (a+0,b+0,b+1,a+1),
            (a+2,a+3,b+3,b+2),
        ]
    faces.append((0,1,3,2))
    e = segments*4
    faces.append((e+0,e+2,e+3,e+1))

    mesh = bpy.data.meshes.new(name+"_Mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.update()

    o = bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(o)
    o.location = center

    axis = Vector(axis)
    if axis.length < 0.001:
        axis = Vector((0,0,1))
    axis.normalize()
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = axis.to_track_quat('Z','Y')
    set_mat(o,material)

    bevel = o.modifiers.new("Bevel","BEVEL")
    bevel.width = max(0.008,thickness*0.22)
    bevel.segments = 2
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception:
        pass
    o.select_set(False)
    return o

def ensure_edit_bone(name, world_head, world_tail, parent_name=None):
    eb = rig.data.edit_bones.get(name) or rig.data.edit_bones.new(name)
    inv = rig.matrix_world.inverted()
    eb.head = inv @ Vector(world_head)
    eb.tail = inv @ Vector(world_tail)
    if (eb.tail-eb.head).length < 0.02:
        eb.tail.z += 0.15
    eb.use_connect = False
    if parent_name:
        parent = rig.data.edit_bones.get(parent_name)
        if parent:
            eb.parent = parent
    return eb

cleanup_v13()

M_GRAPHITE = make_mat("LEAP_FINAL_GraphiteArmor",(0.025,0.029,0.035),0.84,0.25)
M_MECH = make_mat("LEAP_FINAL_MechanicalDark",(0.012,0.014,0.018),0.94,0.20)
M_EYE_GREY = make_mat("LEAP_WP_Eye_Grey",(0.105,0.115,0.125),0.76,0.30)
M_FL_GREY = make_mat("LEAP_WP_FrontL_Grey",(0.095,0.105,0.115),0.78,0.30)
M_FR_GREY = make_mat("LEAP_WP_FrontR_Grey",(0.095,0.105,0.115),0.78,0.30)
M_RL_GREY = make_mat("LEAP_WP_RearL_Grey",(0.090,0.100,0.110),0.80,0.29)
M_RR_GREY = make_mat("LEAP_WP_RearR_Grey",(0.090,0.100,0.110),0.80,0.29)
M_DISCOVERED = make_mat("LEAP_WP_Discovered_PaleYellow",(0.72,0.62,0.30),0.18,0.22,(1.0,0.72,0.20),3.2)
M_HIT = make_mat("LEAP_WP_Hit_WhiteYellow",(0.98,0.90,0.58),0.08,0.16,(1.0,0.90,0.50),9.0)

for leg in ("FL","FR","RL","RR"):
    set_mat(obj(f"{leg}_KneeRing"),M_GRAPHITE)

set_mat(obj("WeakPort_L"),M_GRAPHITE)
set_mat(obj("WeakPort_R"),M_GRAPHITE)
set_mat(obj("RearJumpCore_1"),M_MECH)
set_mat(obj("RearJumpCore_-1"),M_MECH)
set_mat(obj("Eye_OuterRing"),M_GRAPHITE)
set_mat(obj("Eye_InnerRing"),M_MECH)
set_mat(obj("Eye_Lens"),M_MECH)

body_center = world_pos("Core_Body")
eye_center = world_pos("Eye_Lens",body_center+Vector((0.7,0,-0.2)))
fl_hip,fl_knee,fl_ankle = world_pos("FL_HipJoint"),world_pos("FL_KneeJoint"),world_pos("FL_AnkleJoint")
fr_hip,fr_knee,fr_ankle = world_pos("FR_HipJoint"),world_pos("FR_KneeJoint"),world_pos("FR_AnkleJoint")
rear_l = world_pos("RearJumpCore_1",body_center+Vector((-0.7,0.45,0.15)))
rear_r = world_pos("RearJumpCore_-1",body_center+Vector((-0.7,-0.45,0.15)))

def hinge_axis(hip,knee,ankle):
    axis = (Vector(knee)-Vector(hip)).cross(Vector(ankle)-Vector(knee))
    if axis.length < 0.001:
        axis = Vector((0,1,0))
    return axis.normalized()

fl_axis = hinge_axis(fl_hip,fl_knee,fl_ankle)
fr_axis = hinge_axis(fr_hip,fr_knee,fr_ankle)
rear_l_axis = rear_l-body_center
rear_r_axis = rear_r-body_center
if rear_l_axis.length < 0.001: rear_l_axis = Vector((0,1,0))
if rear_r_axis.length < 0.001: rear_r_axis = Vector((0,-1,0))

rig.hide_viewport = False
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
if bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.mode_set(mode='EDIT')

ensure_edit_bone("weak_eye",eye_center,eye_center+Vector((0.18,0,0)),"head")
ensure_edit_bone("cover_eye",eye_center,eye_center+Vector((0.16,0,0)),"head")
ensure_edit_bone("weak_front_L",fl_knee,fl_knee+fl_axis*0.18,"FL_upper")
ensure_edit_bone("cover_front_L",fl_knee,fl_knee+fl_axis*0.16,"FL_upper")
ensure_edit_bone("weak_front_R",fr_knee,fr_knee+fr_axis*0.18,"FR_upper")
ensure_edit_bone("cover_front_R",fr_knee,fr_knee+fr_axis*0.16,"FR_upper")
ensure_edit_bone("weak_rear_L",rear_l,rear_l+rear_l_axis.normalized()*0.18,"rear_power")
ensure_edit_bone("cover_rear_L",rear_l,rear_l+rear_l_axis.normalized()*0.16,"rear_power")
ensure_edit_bone("weak_rear_R",rear_r,rear_r+rear_r_axis.normalized()*0.18,"rear_power")
ensure_edit_bone("cover_rear_R",rear_r,rear_r+rear_r_axis.normalized()*0.16,"rear_power")

bpy.ops.object.mode_set(mode='OBJECT')

eye_arc = create_arc_plate("WP_Eye_Cover",eye_center+Vector((0.01,0,0)),Vector((1,0,0)),0.29,0.39,0.09,-120,120,M_EYE_GREY,22)
rigid_skin(eye_arc,"cover_eye")
fl_arc = create_arc_plate("WP_FrontL_Cover",fl_knee,fl_axis,0.145,0.225,0.08,-105,105,M_FL_GREY,18)
rigid_skin(fl_arc,"cover_front_L")
fr_arc = create_arc_plate("WP_FrontR_Cover",fr_knee,fr_axis,0.145,0.225,0.08,-105,105,M_FR_GREY,18)
rigid_skin(fr_arc,"cover_front_R")
rl_arc = create_arc_plate("WP_RearL_Cover",rear_l,rear_l_axis,0.11,0.185,0.075,-115,115,M_RL_GREY,18)
rigid_skin(rl_arc,"cover_rear_L")
rr_arc = create_arc_plate("WP_RearR_Cover",rear_r,rear_r_axis,0.11,0.185,0.075,-115,115,M_RR_GREY,18)
rigid_skin(rr_arc,"cover_rear_R")

carrier_base = body_center+Vector((-0.08,0,0))
add_tiny_carrier("WPV13_MaterialCarrier_Discovered",carrier_base+Vector((0,0.015,0)),M_DISCOVERED)
add_tiny_carrier("WPV13_MaterialCarrier_Hit",carrier_base+Vector((0,-0.015,0)),M_HIT)

root["WeakPointVersion"] = "1.3"
root["WeakPointStyle"] = "Dormant grey -> pale yellow discovered -> white-yellow hit flash"
root["BreakableCovers"] = "cover_eye,cover_front_L,cover_front_R,cover_rear_L,cover_rear_R"
root["WeakPointBones"] = "weak_eye,weak_front_L,weak_front_R,weak_rear_L,weak_rear_R"
root["LootIntent"] = "Hide broken cover bone in Unreal and spawn loot pickup"

bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root

print("AFTERFALL Leaper V1.3 weak-point patch complete.")
