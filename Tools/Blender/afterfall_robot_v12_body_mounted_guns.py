import bpy
import math
from mathutils import Vector, Matrix, Euler

# AFTERFALL - GUN PLATFORM V1.2 BODY-MOUNTED WEAPONS
# Blender 5.2+
# Fixes weapon placement by deriving mounts from current Thorax_Core
# and attaching weapon pivots to the V07 body bone.

ROOT_NAME = "LEAPER_ROOT"
RIG_NAME  = "ARM_Leaper_GameRig_V07"
BODY_NAME = "Thorax_Core"

root = bpy.data.objects.get(ROOT_NAME)
rig  = bpy.data.objects.get(RIG_NAME)
body = bpy.data.objects.get(BODY_NAME)

if not root:
    raise RuntimeError("LEAPER_ROOT not found.")
if not rig or rig.type != 'ARMATURE':
    raise RuntimeError("ARM_Leaper_GameRig_V07 not found.")
if not body:
    raise RuntimeError("Thorax_Core not found.")

scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()

for o in list(bpy.data.objects):
    if o.name.startswith("GUN_"):
        bpy.data.objects.remove(o, do_unlink=True)

def mat(name):
    return bpy.data.materials.get(name)

M_ARMOR  = mat("M_Armor_BoneWhite")
M_ARMOR2 = mat("M_Armor_DarkWhite")
M_DARK   = mat("M_Mechanical_Dark")
M_ORANGE = mat("M_Accent_Orange")
M_RED    = mat("M_Sensor_Red")
M_HYD    = mat("M_Hydraulic")

body_world = body.matrix_world.copy()
body_rot = body_world.to_quaternion()

def world_point(local_xyz):
    return body_world @ Vector(local_xyz)

def world_rot(local_euler=(0,0,0)):
    q_local = Euler(local_euler, 'XYZ').to_quaternion()
    return body_rot @ q_local

def parent_keep_world(child, parent, bone_name=None):
    world = child.matrix_world.copy()
    if bone_name:
        child.parent = parent
        child.parent_type = 'BONE'
        child.parent_bone = bone_name
    else:
        child.parent = parent
        child.parent_type = 'OBJECT'
    child.matrix_world = world

def add_empty(name, world_loc, parent=None, bone_name=None, size=0.16):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=world_loc)
    o = bpy.context.object
    o.name = name
    o.empty_display_size = size
    if parent:
        parent_keep_world(o, parent, bone_name)
    return o

def add_box_local(name, local_loc, local_scale, material, bevel=0.05, local_rot=(0,0,0), parent=None):
    p = world_point(local_loc)
    q = world_rot(local_rot)
    bpy.ops.mesh.primitive_cube_add(location=p)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = q
    o.scale = local_scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bev = o.modifiers.new("Bevel", "BEVEL")
    bev.width = bevel
    bev.segments = 3
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=bev.name)
    if material:
        o.data.materials.append(material)
    if parent:
        parent_keep_world(o, parent)
    return o

def add_cyl_local(name, local_a, local_b, radius, material, verts=16, parent=None):
    a = world_point(local_a)
    b = world_point(local_b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=d.length, location=(a+b)/2)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z','Y')
    if material:
        o.data.materials.append(material)
    if parent:
        parent_keep_world(o, parent)
    return o

def add_torus_local(name, local_loc, major, minor, material, local_rot=(0,0,0), parent=None):
    p = world_point(local_loc)
    q = world_rot(local_rot)
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=20, minor_segments=8, location=p)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = q
    if material:
        o.data.materials.append(material)
    if parent:
        parent_keep_world(o, parent)
    return o

for side in (-1, 1):
    label = "L" if side > 0 else "R"
    pivot = add_empty(f"GUN_{label}_PIVOT", world_point((0.20,0.78*side,0.34)), rig, "body", 0.18)

    add_box_local(f"GUN_{label}_HOUSING",(0.38,0.78*side,0.35),(0.34,0.17,0.14),M_ARMOR2,0.055,(0,math.radians(-4),math.radians(-2*side)),pivot)
    add_box_local(f"GUN_{label}_ARMOR_CAP",(0.34,0.78*side,0.49),(0.28,0.15,0.055),M_ARMOR,0.04,(0,math.radians(-5),math.radians(-2*side)),pivot)
    add_box_local(f"GUN_{label}_AMMO_BOX",(0.03,0.78*side,0.35),(0.16,0.18,0.17),M_ARMOR,0.05,parent=pivot)
    add_cyl_local(f"GUN_{label}_BARREL_SHROUD",(0.58,0.78*side,0.34),(1.02,0.78*side,0.30),0.075,M_DARK,16,pivot)
    add_cyl_local(f"GUN_{label}_BARREL",(0.88,0.78*side,0.30),(1.62,0.78*side,0.23),0.040,M_HYD if M_HYD else M_DARK,12,pivot)
    add_torus_local(f"GUN_{label}_MUZZLE_RING",(1.63,0.78*side,0.23),0.072,0.017,M_ORANGE,(0,math.radians(90),0),pivot)
    add_torus_local(f"GUN_{label}_AIM_SENSOR",(0.57,0.78*side,0.15),0.043,0.013,M_RED,(0,math.radians(90),0),pivot)

    brace = add_cyl_local(f"GUN_{label}_BRACE",(-0.05,0.52*side,0.08),(0.18,0.76*side,0.30),0.040,M_DARK,12,None)
    parent_keep_world(brace, rig, "body")

    add_empty(f"GUN_MUZZLE_{label}", world_point((1.68,0.78*side,0.23)), pivot, None, 0.075)

mast = add_box_local("GUN_TARGET_MAST",(0.05,0,0.73),(0.09,0.08,0.15),M_DARK,0.03,(0,math.radians(-4),0),None)
parent_keep_world(mast, rig, "body")

sensor = add_torus_local("GUN_TARGET_SENSOR",(0.16,0,0.73),0.050,0.013,M_RED,(0,math.radians(90),0),None)
parent_keep_world(sensor, rig, "body")

root["EnemyRole"] = "Ranged gun platform"
root["WeaponSystem"] = "Twin body-mounted autocannons"
root["WeaponPatchVersion"] = "1.2"
root["JumpRole"] = "Removed - dedicated pounce creature"

print("AFTERFALL Gun Platform V1.2 mounted successfully.")