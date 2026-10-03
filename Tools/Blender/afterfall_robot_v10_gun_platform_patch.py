import bpy
import math
from mathutils import Vector

# AFTERFALL - SIX-LEGGED GUN PLATFORM V1.0 WEAPON PATCH
# Run on top of the current refined Leaper/robot scene.
# Keeps the robot body and adds twin shoulder-mounted autocannons,
# ammo housings, barrels, muzzle rings and simple weapon pivots.
# Does NOT delete the existing robot.

ROOT_NAME = "LEAPER_ROOT"
root = bpy.data.objects.get(ROOT_NAME)
if not root:
    raise RuntimeError("LEAPER_ROOT not found. Open the current robot scene first.")

def get(name):
    return bpy.data.objects.get(name)

def mat(name):
    return bpy.data.materials.get(name)

M_ARMOR  = mat("M_Armor_BoneWhite")
M_ARMOR2 = mat("M_Armor_DarkWhite")
M_DARK   = mat("M_Mechanical_Dark")
M_ORANGE = mat("M_Accent_Orange")
M_RED    = mat("M_Sensor_Red")
M_HYD    = mat("M_Hydraulic")

def add_box(name, loc, scale, material, bevel=0.05, rot=(0,0,0), parent=root):
    if get(name):
        return get(name)
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o=bpy.context.object
    o.name=name
    o.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b=o.modifiers.new("Bevel","BEVEL")
    b.width=bevel
    b.segments=3
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.modifier_apply(modifier=b.name)
    if material:
        o.data.materials.append(material)
    if parent:
        o.parent=parent
    return o

def add_cyl_between(name, a, b, radius, material, verts=16, parent=root):
    if get(name):
        return get(name)
    a=Vector(a); b=Vector(b)
    d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=d.length, location=(a+b)/2)
    o=bpy.context.object
    o.name=name
    o.rotation_mode='QUATERNION'
    o.rotation_quaternion=d.to_track_quat('Z','Y')
    if material:
        o.data.materials.append(material)
    if parent:
        o.parent=parent
    return o

def add_torus(name, loc, major, minor, material, rot=(0,0,0), parent=root):
    if get(name):
        return get(name)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major,
        minor_radius=minor,
        major_segments=20,
        minor_segments=8,
        location=loc,
        rotation=rot
    )
    o=bpy.context.object
    o.name=name
    if material:
        o.data.materials.append(material)
    if parent:
        o.parent=parent
    return o

for side in (-1, 1):
    label = "L" if side > 0 else "R"
    y = 0.82 * side

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.72, y, 1.78))
    pivot=bpy.context.object
    pivot.name=f"GUN_{label}_PIVOT"
    pivot.empty_display_size=0.18
    pivot.parent=root

    add_box(
        f"GUN_{label}_HOUSING",
        (0.84,y,1.80),
        (0.42,0.20,0.17),
        M_ARMOR2,0.06,
        rot=(0,math.radians(-5),math.radians(-2*side)),
        parent=pivot
    )

    add_box(
        f"GUN_{label}_AMMO_BOX",
        (0.42,y,1.84),
        (0.22,0.22,0.20),
        M_ARMOR,0.06,
        parent=pivot
    )

    add_cyl_between(
        f"GUN_{label}_BARREL_OUTER",
        (1.06,y,1.78),
        (2.05,y,1.70),
        0.075,M_DARK,16,pivot
    )
    add_cyl_between(
        f"GUN_{label}_BARREL_INNER",
        (1.55,y,1.70),
        (2.18,y,1.65),
        0.038,M_HYD if M_HYD else M_DARK,12,pivot
    )

    add_torus(
        f"GUN_{label}_MUZZLE_RING",
        (2.18,y,1.65),
        0.095,0.022,
        M_ORANGE,
        rot=(0,math.radians(90),0),
        parent=pivot
    )

    add_torus(
        f"GUN_{label}_AIM_SENSOR",
        (1.00,y,1.59),
        0.055,0.015,
        M_RED,
        rot=(0,math.radians(90),0),
        parent=pivot
    )

    add_cyl_between(
        f"GUN_{label}_BRACE",
        (0.50,0.62*side,1.58),
        (0.78,y,1.74),
        0.045,M_DARK,12,root
    )

add_box(
    "GUN_TARGET_MAST",
    (0.18,0,2.33),
    (0.11,0.10,0.20),
    M_DARK,0.04,
    rot=(0,math.radians(-4),0)
)

root["EnemyRole"]="Ranged gun platform"
root["WeaponSystem"]="Twin shoulder autocannons"
root["JumpRole"]="Removed from this robot; reserved for separate creature"

print("AFTERFALL gun-platform weapon patch added successfully.")
