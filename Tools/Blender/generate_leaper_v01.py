import bpy
import math
from mathutils import Vector

# AFTERFALL - Leaper V0.1 procedural blockout
# Blender 5.2.x compatible
# Creates an original mobile-friendly six-legged robot blockout for gameplay prototyping.

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def mat(name, base, metallic=0.0, rough=0.5, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return m

def rounded_box(name, loc, scale, material, bevel=0.12):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bev = o.modifiers.new("Bevel", "BEVEL")
    bev.width = bevel
    bev.segments = 3
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=bev.name)
    if material:
        o.data.materials.append(material)
    return o

def cyl_between(name, a, b, radius, material, vertices=12):
    a = Vector(a)
    b = Vector(b)
    mid = (a + b) / 2.0
    direction = b - a
    length = direction.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=length, location=mid)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = direction.to_track_quat('Z', 'Y')
    if material:
        o.data.materials.append(material)
    return o

def sphere(name, loc, radius, material, segments=24, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=loc)
    o = bpy.context.object
    o.name = name
    if material:
        o.data.materials.append(material)
    return o

def parent(child, parent_obj):
    child.parent = parent_obj

clear_scene()
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

MAT_ARMOR = mat("M_Armor_White", (0.55, 0.52, 0.48), metallic=0.65, rough=0.32)
MAT_DARK = mat("M_Mechanical_Dark", (0.035, 0.035, 0.045), metallic=0.85, rough=0.22)
MAT_ORANGE = mat("M_Accent_Orange", (0.45, 0.055, 0.01), metallic=0.55, rough=0.3)
MAT_RED = mat("M_Sensor_Red", (0.06, 0.005, 0.001), metallic=0.1, rough=0.25, emission=(1.0, 0.025, 0.001), emission_strength=8.0)

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,1.7))
root = bpy.context.object
root.name = "LEAPER_ROOT"

body = rounded_box("Leaper_Thorax", (0,0,1.85), (1.35,0.90,0.42), MAT_DARK, 0.18); parent(body, root)
armor_top = rounded_box("Armor_Top", (-0.05,0,2.22), (1.18,0.82,0.16), MAT_ARMOR, 0.16); parent(armor_top, root)
armor_front = rounded_box("Armor_Front", (1.22,0,1.92), (0.42,0.72,0.30), MAT_ARMOR, 0.14); armor_front.rotation_euler[1] = math.radians(-12); parent(armor_front, root)
armor_rear = rounded_box("Armor_Rear", (-1.18,0,1.95), (0.40,0.72,0.28), MAT_ARMOR, 0.14); armor_rear.rotation_euler[1] = math.radians(10); parent(armor_rear, root)
head = rounded_box("Sensor_Head", (1.65,0,1.74), (0.38,0.55,0.28), MAT_DARK, 0.12); parent(head, root)

for i,p in enumerate([(2.00,0.00,1.80),(1.93,0.23,1.78),(1.93,-0.23,1.78),(1.90,0.00,1.58)],1):
    s = sphere(f"Sensor_{i}", p, 0.12 if i==1 else 0.095, MAT_RED, 16, 8); parent(s, root)

for side in (-1,1):
    act = cyl_between(f"JumpActuator_{side}", (-0.85,0.50*side,2.05), (-1.45,0.62*side,1.60), 0.13, MAT_ORANGE, 16); parent(act, root)
    core = sphere(f"JumpActuatorCore_{side}", (-1.05,0.54*side,1.94), 0.16, MAT_RED, 16, 8); core.scale.z=0.65; parent(core, root)

leg_defs = [
    ("FL",(0.85,0.65,1.72),(1.55,1.35,1.15),(2.10,1.90,0.28)),
    ("FR",(0.85,-0.65,1.72),(1.55,-1.35,1.15),(2.10,-1.90,0.28)),
    ("ML",(0.00,0.78,1.70),(0.15,1.55,0.95),(0.55,2.10,0.22)),
    ("MR",(0.00,-0.78,1.70),(0.15,-1.55,0.95),(0.55,-2.10,0.22)),
    ("RL",(-0.90,0.65,1.72),(-1.45,1.45,1.05),(-2.15,1.90,0.24)),
    ("RR",(-0.90,-0.65,1.72),(-1.45,-1.45,1.05),(-2.15,-1.90,0.24)),
]
for name,hip,knee,foot in leg_defs:
    for o in (
        sphere(f"{name}_Hip", hip, 0.17, MAT_ORANGE, 16, 8),
        sphere(f"{name}_Knee", knee, 0.15, MAT_ORANGE, 16, 8),
        sphere(f"{name}_Ankle", foot, 0.12, MAT_ORANGE, 16, 8),
        cyl_between(f"{name}_UpperLeg", hip, knee, 0.11, MAT_DARK, 12),
        cyl_between(f"{name}_LowerLeg", knee, foot, 0.095, MAT_DARK, 12)
    ): parent(o, root)

bpy.ops.object.armature_add(enter_editmode=True, location=(0,0,0))
arm = bpy.context.object
arm.name = "ARM_Leaper_Blockout"
arm.show_in_front = True
eb = arm.data.edit_bones
eb.remove(eb[0])
rb = eb.new("root"); rb.head=(0,0,0); rb.tail=(0,0,1.2)
bb = eb.new("body"); bb.head=(0,0,1.2); bb.tail=(0,0,2.1); bb.parent=rb
for name,hip,knee,foot in leg_defs:
    b1=eb.new(f"{name}_upper"); b1.head=hip; b1.tail=knee; b1.parent=bb
    b2=eb.new(f"{name}_lower"); b2.head=knee; b2.tail=foot; b2.parent=b1
    toe=(Vector(foot)+Vector((0.35 if foot[0]>=0 else -0.35,0,0))).to_tuple()
    b3=eb.new(f"{name}_foot"); b3.head=foot; b3.tail=toe; b3.parent=b2
bpy.ops.object.mode_set(mode='OBJECT')
parent(arm, root)

root["EnemyType"]="Leaper"
root["PrototypeVersion"]="0.1"
root["TargetPlatform"]="Android"
root["GameplayWeakPoints"]="Rear jump actuators, sensor cluster, leg joints"

bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active=root
print("AFTERFALL Leaper V0.1 blockout generated successfully.")
