import bpy
import math
from mathutils import Vector

# AFTERFALL - LEAPER V0.2
# Refined six-legged mobile-friendly blockout.
# Blender 5.2+.
# Run in a fresh Blender scene or let this script clear the current scene.

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def mk_mat(name, color, metallic=0.0, roughness=0.45, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = strength
    return m

def add_box(name, loc, scale, mat, bevel=0.08, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod = o.modifiers.new("Bevel", "BEVEL")
    mod.width = bevel
    mod.segments = 3
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(mat)
    return o

def add_sphere(name, loc, radius, mat, seg=20, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=radius, location=loc)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    return o

def add_cyl_between(name, a, b, radius, mat, verts=12):
    a, b = Vector(a), Vector(b)
    d = b-a
    mid = (a+b)*0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=d.length, location=mid)
    o = bpy.context.object
    o.name = name
    o.rotation_mode='QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z','Y')
    o.data.materials.append(mat)
    return o

def add_cone_between(name, a, b, r1, r2, mat, verts=10):
    a,b = Vector(a),Vector(b)
    d=b-a
    mid=(a+b)*0.5
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d.length, location=mid)
    o=bpy.context.object
    o.name=name
    o.rotation_mode='QUATERNION'
    o.rotation_quaternion=d.to_track_quat('Z','Y')
    o.data.materials.append(mat)
    return o

def add_plate(name, loc, scale, rot, mat, bevel=0.07):
    return add_box(name, loc, scale, mat, bevel, rot)

def parent_all(objs, parent):
    for o in objs:
        o.parent = parent

clear_scene()
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1.0

M_ARMOR = mk_mat("M_Armor_BoneWhite",(0.62,0.58,0.52), metallic=0.55, roughness=0.32)
M_DARK  = mk_mat("M_Mechanical",(0.035,0.04,0.05), metallic=0.9, roughness=0.22)
M_ORANGE= mk_mat("M_Accent_Orange",(0.52,0.07,0.012), metallic=0.55, roughness=0.28)
M_RED   = mk_mat("M_Core_Red",(0.05,0.002,0.001), metallic=0.1, roughness=0.2,
                 emission=(1.0,0.02,0.001), strength=10)

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,1.55))
ROOT=bpy.context.object
ROOT.name="LEAPER_ROOT"
ROOT.empty_display_size=0.35

parts=[]
parts.append(add_box("Thorax_Core",(0,0,1.62),(1.28,0.84,0.34),M_DARK,0.16))
parts.append(add_box("Thorax_Upper",(-0.10,0,1.94),(1.06,0.75,0.18),M_ARMOR,0.14))
parts.append(add_box("Thorax_Rear",(-1.05,0,1.67),(0.42,0.68,0.28),M_ARMOR,0.12,rot=(0,math.radians(10),0)))
parts.append(add_box("Thorax_Front",(1.05,0,1.66),(0.45,0.65,0.27),M_ARMOR,0.12,rot=(0,math.radians(-12),0)))
parts.append(add_plate("Armor_Top_L",(-0.12,0.42,2.08),(0.90,0.28,0.09),(0,math.radians(-5),math.radians(2)),M_ARMOR))
parts.append(add_plate("Armor_Top_R",(-0.12,-0.42,2.08),(0.90,0.28,0.09),(0,math.radians(-5),math.radians(-2)),M_ARMOR))

for i,x in enumerate([-0.70,-0.40,-0.10,0.20]):
    parts.append(add_box(f"SpineVent_{i}",(x,0,2.16),(0.09,0.25,0.06),M_DARK,0.03))

parts.append(add_box("Head_Main",(1.58,0,1.58),(0.42,0.50,0.25),M_DARK,0.13,rot=(0,math.radians(-8),0)))
parts.append(add_box("Head_Armor",(1.62,0,1.78),(0.38,0.46,0.12),M_ARMOR,0.10,rot=(0,math.radians(-10),0)))

sensor_pts=[
    (1.98,0,1.62,0.12),
    (1.91,0.22,1.65,0.085),
    (1.91,-0.22,1.65,0.085),
    (1.91,0.15,1.45,0.075),
    (1.91,-0.15,1.45,0.075)
]
for i,(x,y,z,r) in enumerate(sensor_pts):
    parts.append(add_sphere(f"Sensor_{i}",(x,y,z),r,M_RED,16,8))

for s in (-1,1):
    a=(1.62,0.33*s,1.42)
    b=(1.95,0.48*s,1.25)
    c=(2.18,0.54*s,1.16)
    parts.append(add_cyl_between(f"MandibleArm_{s}",a,b,0.055,M_DARK,10))
    parts.append(add_cone_between(f"MandibleTip_{s}",b,c,0.07,0.012,M_ORANGE,8))

for s in (-1,1):
    parts.append(add_cyl_between(f"JumpCylinder_{s}",(-0.70,0.50*s,1.87),(-1.35,0.63*s,1.34),0.13,M_ORANGE,16))
    parts.append(add_cyl_between(f"JumpPiston_{s}",(-1.05,0.56*s,1.60),(-1.60,0.72*s,1.12),0.07,M_DARK,12))
    parts.append(add_sphere(f"JumpCore_{s}",(-0.93,0.54*s,1.70),0.15,M_RED,16,8))
    parts.append(add_plate(f"JumpArmor_{s}",(-1.02,0.68*s,1.85),(0.42,0.17,0.10),
                           (0,math.radians(18),math.radians(8*s)),M_ARMOR))

legs=[
    ("FL",(0.78,0.62,1.60),(1.55,1.20,1.05),(2.05,1.80,0.33),(2.48,1.96,0.20)),
    ("FR",(0.78,-0.62,1.60),(1.55,-1.20,1.05),(2.05,-1.80,0.33),(2.48,-1.96,0.20)),
    ("ML",(0.00,0.76,1.56),(0.20,1.48,0.95),(0.55,2.05,0.28),(0.86,2.34,0.16)),
    ("MR",(0.00,-0.76,1.56),(0.20,-1.48,0.95),(0.55,-2.05,0.28),(0.86,-2.34,0.16)),
    ("RL",(-0.82,0.62,1.58),(-1.42,1.28,1.04),(-2.00,1.76,0.31),(-2.45,1.88,0.18)),
    ("RR",(-0.82,-0.62,1.58),(-1.42,-1.28,1.04),(-2.00,-1.76,0.31),(-2.45,-1.88,0.18)),
]

for name,hip,knee,ankle,toe in legs:
    parts.append(add_sphere(f"{name}_HipJoint",hip,0.15,M_ORANGE,16,8))
    parts.append(add_sphere(f"{name}_KneeJoint",knee,0.14,M_ORANGE,16,8))
    parts.append(add_sphere(f"{name}_AnkleJoint",ankle,0.10,M_DARK,14,7))
    parts.append(add_cyl_between(f"{name}_Upper",hip,knee,0.105,M_DARK,12))
    parts.append(add_cyl_between(f"{name}_Lower",knee,ankle,0.09,M_DARK,12))
    parts.append(add_cone_between(f"{name}_Claw",ankle,toe,0.07,0.015,M_DARK,9))
    v1=Vector(hip); v2=Vector(knee)
    side=(Vector((0,0,1)).cross(v2-v1)).normalized()*0.08
    parts.append(add_cyl_between(f"{name}_Hydraulic",v1+side,v2+side,0.035,M_ORANGE,10))
    mid=(v1+v2)*0.5
    plate=add_box(f"{name}_Armor",mid,(0.34,0.12,0.09),M_ARMOR,0.07)
    plate.rotation_mode='QUATERNION'
    plate.rotation_quaternion=(v2-v1).to_track_quat('X','Z')
    parts.append(plate)

parts.append(add_plate("HipArmor_L",(0.18,0.87,1.65),(0.64,0.16,0.18),(0,0,math.radians(3)),M_ARMOR))
parts.append(add_plate("HipArmor_R",(0.18,-0.87,1.65),(0.64,0.16,0.18),(0,0,math.radians(-3)),M_ARMOR))

for o in parts:
    o.parent=ROOT

weak_points=[
    ("WP_Sensor",(1.98,0,1.62)),
    ("WP_Jump_L",(-0.93,0.54,1.70)),
    ("WP_Jump_R",(-0.93,-0.54,1.70)),
]
for n,loc in weak_points:
    bpy.ops.object.empty_add(type='SPHERE', location=loc)
    e=bpy.context.object
    e.name=n
    e.empty_display_size=0.16
    e.parent=ROOT

ROOT["EnemyType"]="Leaper"
ROOT["PrototypeVersion"]="0.2"
ROOT["TargetPlatform"]="Android"
ROOT["GameplayWeakPoints"]="sensor, jump actuators, leg joints"

bpy.ops.object.select_all(action='DESELECT')
ROOT.select_set(True)
bpy.context.view_layer.objects.active=ROOT
print("AFTERFALL Leaper V0.2 generated.")