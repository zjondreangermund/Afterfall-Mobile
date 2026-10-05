import bpy
import math
from mathutils import Vector

# AFTERFALL - LEAPER V0.4 FULL GENERATOR
# Blender 5.2+ / Unreal-friendly procedural blockout
# Rebuilds the Leaper from scratch with layered armor, stronger jump actuators,
# thicker legs, exposed hydraulics/cables, sharper claws, weak points and armature.

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def get_principled(mat):
    if not mat.use_nodes:
        mat.use_nodes = True
    return mat.node_tree.nodes.get("Principled BSDF")

def make_mat(name, base, metallic=0.0, rough=0.5, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = get_principled(mat)
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metallic
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = rough
    if emission and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
    if emission and "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

def add_box(name, loc, scale, mat, bevel=0.08, rot=(0,0,0), parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bev = o.modifiers.new("Bevel", "BEVEL")
    bev.width = bevel
    bev.segments = 3
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=bev.name)
    o.data.materials.append(mat)
    if parent: o.parent = parent
    return o

def add_sphere(name, loc, radius, mat, seg=20, rings=10, scale=(1,1,1), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=radius, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if parent: o.parent = parent
    return o

def add_cyl_between(name, a, b, radius, mat, verts=12, parent=None):
    a = Vector(a); b = Vector(b); d = b-a
    if d.length < 0.0001: return None
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=d.length, location=(a+b)*0.5)
    o = bpy.context.object
    o.name = name
    o.rotation_mode='QUATERNION'
    o.rotation_quaternion=d.to_track_quat('Z','Y')
    o.data.materials.append(mat)
    if parent: o.parent=parent
    return o

def add_cone_between(name, a, b, r1, r2, mat, verts=10, parent=None):
    a=Vector(a); b=Vector(b); d=b-a
    if d.length < 0.0001: return None
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r1,radius2=r2,depth=d.length,location=(a+b)*0.5)
    o=bpy.context.object
    o.name=name
    o.rotation_mode='QUATERNION'
    o.rotation_quaternion=d.to_track_quat('Z','Y')
    o.data.materials.append(mat)
    if parent: o.parent=parent
    return o

def add_torus(name, loc, major_radius, minor_radius, mat, rot=(0,0,0), parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius,minor_radius=minor_radius,
        major_segments=20,minor_segments=8,location=loc,rotation=rot)
    o=bpy.context.object
    o.name=name
    o.data.materials.append(mat)
    if parent: o.parent=parent
    return o

def add_cable(name, points, radius, mat, parent=None):
    curve=bpy.data.curves.new(name+"_Curve",type='CURVE')
    curve.dimensions='3D'
    curve.bevel_depth=radius
    curve.bevel_resolution=2
    spline=curve.splines.new('BEZIER')
    spline.bezier_points.add(len(points)-1)
    for bp,co in zip(spline.bezier_points,points):
        bp.co=co
        bp.handle_left_type='AUTO'
        bp.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,curve)
    bpy.context.collection.objects.link(o)
    curve.materials.append(mat)
    if parent: o.parent=parent
    return o

def add_empty(name, loc, size=0.16, parent=None):
    bpy.ops.object.empty_add(type='SPHERE',location=loc)
    e=bpy.context.object
    e.name=name
    e.empty_display_size=size
    if parent: e.parent=parent
    return e

clear_scene()
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1.0
scene.render.engine='BLENDER_EEVEE'

# Shared industrial robot palette. Keep legacy material names because later
# weapon/rig scripts look them up by name.
M_ARMOR=make_mat("M_Armor_BoneWhite",(0.285,0.315,0.345),0.96,0.29)
M_ARMOR2=make_mat("M_Armor_DarkWhite",(0.145,0.165,0.185),0.92,0.38)
M_DARK=make_mat("M_Mechanical_Dark",(0.075,0.088,0.102),0.94,0.42)
M_ORANGE=make_mat("M_Accent_Orange",(0.52,0.12,0.018),0.70,0.31)
M_RED=make_mat("M_Sensor_Red",(0.80,0.025,0.012),0.08,0.15,(1.0,0.015,0.008),10.0)
M_CABLE=make_mat("M_Cable",(0.025,0.028,0.032),0.22,0.62)
M_HYD=make_mat("M_Hydraulic",(0.36,0.39,0.42),0.98,0.20)
M_BLUE=make_mat("M_PlayerRef",(0.03,0.12,0.25),0.0,0.65)

bpy.ops.object.empty_add(type='PLAIN_AXES',location=(0,0,1.45))
ROOT=bpy.context.object
ROOT.name="LEAPER_ROOT"
ROOT.empty_display_size=0.35
ROOT["MachineMaterialStandard"]="Industrial Titanium / Steel"
ROOT["MachineMaterialPaletteVersion"]="1.0"
ROOT["MachineSignalRule"]="White scan; yellow alert; red attack."

add_box("Thorax_Core",(0,0,1.48),(1.30,0.86,0.32),M_DARK,0.16,parent=ROOT)
add_box("Armor_Center",(-0.15,0,1.86),(0.98,0.64,0.16),M_ARMOR,0.14,
        rot=(0,math.radians(-4),0),parent=ROOT)
for i,(x,z,sx,sy,rz) in enumerate([(-0.65,2.03,0.52,0.62,8),(-0.15,2.07,0.58,0.68,0),(0.42,2.02,0.48,0.60,-8)]):
    add_box(f"TopPlate_{i}",(x,0,z),(sx,sy,0.085),M_ARMOR,0.07,
            rot=(0,math.radians(-5),math.radians(rz)),parent=ROOT)
for side in (-1,1):
    y=0.74*side
    add_box(f"SideArmor_F_{side}",(0.55,y,1.63),(0.52,0.16,0.22),M_ARMOR,0.08,
            rot=(math.radians(6*side),math.radians(-10),math.radians(-5*side)),parent=ROOT)
    add_box(f"SideArmor_R_{side}",(-0.60,y,1.64),(0.50,0.16,0.22),M_ARMOR2,0.08,
            rot=(math.radians(-5*side),math.radians(10),math.radians(5*side)),parent=ROOT)
add_box("Rear_Housing",(-1.18,0,1.50),(0.38,0.66,0.27),M_ARMOR2,0.12,
        rot=(0,math.radians(16),0),parent=ROOT)
for i,x in enumerate([-0.65,-0.35,-0.05,0.25,0.50]):
    add_box(f"SpineVent_{i}",(x,0,2.16),(0.07,0.24,0.055),M_DARK,0.025,parent=ROOT)

add_box("Head_Base",(1.42,0,1.40),(0.46,0.50,0.25),M_DARK,0.13,
        rot=(0,math.radians(-12),0),parent=ROOT)
add_box("Head_Armor",(1.55,0,1.62),(0.44,0.48,0.12),M_ARMOR,0.10,
        rot=(0,math.radians(-18),0),parent=ROOT)
for side in (-1,1):
    add_box(f"Brow_{side}",(1.79,0.28*side,1.58),(0.26,0.15,0.10),M_ARMOR2,0.06,
            rot=(math.radians(8*side),math.radians(-14),math.radians(8*side)),parent=ROOT)

add_sphere("Sensor_Main",(1.96,0,1.46),0.13,M_RED,18,9,parent=ROOT)
for i,(y,z,r) in enumerate([(0.24,1.50,0.09),(-0.24,1.50,0.09),(0.15,1.29,0.075),(-0.15,1.29,0.075)]):
    add_sphere(f"Sensor_Aux_{i}",(1.90,y,z),r,M_RED,16,8,parent=ROOT)
add_torus("Sensor_Main_Ring",(1.965,0,1.46),0.16,0.025,M_ORANGE,
          rot=(0,math.radians(90),0),parent=ROOT)
for side in (-1,1):
    a=(1.55,0.30*side,1.31); b=(1.94,0.44*side,1.18); c=(2.22,0.52*side,1.09)
    add_cyl_between(f"MandibleArm_{side}",a,b,0.060,M_DARK,10,ROOT)
    add_cone_between(f"MandibleClaw_{side}",b,c,0.075,0.012,M_ORANGE,9,ROOT)

for side in (-1,1):
    add_cyl_between(f"JumpActuator_{side}",(-0.70,0.50*side,1.86),(-1.42,0.67*side,1.22),0.145,M_ORANGE,16,ROOT)
    add_cyl_between(f"JumpPiston_{side}",(-1.03,0.58*side,1.56),(-1.67,0.78*side,1.00),0.072,M_HYD,12,ROOT)
    add_sphere(f"JumpCore_{side}",(-0.97,0.55*side,1.68),0.16,M_RED,16,8,parent=ROOT)
    add_torus(f"JumpCoreRing_{side}",(-0.97,0.55*side,1.68),0.20,0.025,M_DARK,
              rot=(math.radians(90),0,0),parent=ROOT)
    add_box(f"JumpArmor_{side}",(-1.02,0.69*side,1.84),(0.44,0.18,0.11),M_ARMOR,0.08,
            rot=(math.radians(4*side),math.radians(18),math.radians(9*side)),parent=ROOT)

legs=[
("FL",(0.78,0.64,1.54),(1.52,1.22,1.03),(2.07,1.82,0.35),(2.55,2.02,0.18)),
("FR",(0.78,-0.64,1.54),(1.52,-1.22,1.03),(2.07,-1.82,0.35),(2.55,-2.02,0.18)),
("ML",(0.00,0.78,1.52),(0.18,1.50,0.91),(0.58,2.08,0.28),(0.92,2.40,0.15)),
("MR",(0.00,-0.78,1.52),(0.18,-1.50,0.91),(0.58,-2.08,0.28),(0.92,-2.40,0.15)),
("RL",(-0.82,0.64,1.54),(-1.43,1.30,1.02),(-2.06,1.79,0.33),(-2.55,1.98,0.17)),
("RR",(-0.82,-0.64,1.54),(-1.43,-1.30,1.02),(-2.06,-1.79,0.33),(-2.55,-1.98,0.17)),
]
for name,hip,knee,ankle,toe in legs:
    add_sphere(f"{name}_HipJoint",hip,0.16,M_ORANGE,16,8,parent=ROOT)
    add_sphere(f"{name}_KneeJoint",knee,0.145,M_ORANGE,16,8,parent=ROOT)
    add_sphere(f"{name}_AnkleJoint",ankle,0.105,M_DARK,14,7,parent=ROOT)
    add_cyl_between(f"{name}_Upper",hip,knee,0.115,M_DARK,12,ROOT)
    add_cyl_between(f"{name}_Lower",knee,ankle,0.098,M_DARK,12,ROOT)
    hv1=Vector(hip); hv2=Vector(knee)
    sidev=Vector((0,0,1)).cross(hv2-hv1)
    if sidev.length: sidev.normalize()
    sidev*=0.09
    add_cyl_between(f"{name}_Hydraulic",hv1+sidev,hv2+sidev,0.038,M_HYD,10,ROOT)
    add_cable(f"{name}_Cable",[tuple(hv1+sidev*1.6),tuple((hv1+hv2)*0.5+sidev*1.9+Vector((0,0,0.05))),tuple(hv2+sidev*1.5)],0.018,M_CABLE,ROOT)
    mid=(hv1+hv2)*0.5
    plate=add_box(f"{name}_UpperArmor",mid,(0.36,0.13,0.10),M_ARMOR,0.07,parent=ROOT)
    plate.rotation_mode='QUATERNION'
    plate.rotation_quaternion=(hv2-hv1).to_track_quat('X','Z')
    add_box(f"{name}_KneeArmor",knee,(0.20,0.15,0.12),M_ARMOR2,0.06,parent=ROOT)
    add_cone_between(f"{name}_MainClaw",ankle,toe,0.075,0.010,M_DARK,9,ROOT)

for name,loc,rot in [
("Shoulder_FL",(0.60,0.84,1.58),(8,-12,-18)),
("Shoulder_FR",(0.60,-0.84,1.58),(-8,-12,18)),
("Shoulder_RL",(-0.66,0.84,1.56),(8,12,18)),
("Shoulder_RR",(-0.66,-0.84,1.56),(-8,12,-18)),
]:
    add_box(name,loc,(0.36,0.17,0.17),M_ARMOR,0.07,
            rot=tuple(math.radians(v) for v in rot),parent=ROOT)

add_sphere("Belly_Core",(0.22,0,1.18),0.18,M_RED,18,9,parent=ROOT)
add_torus("Belly_Core_Ring",(0.22,0,1.18),0.225,0.026,M_ORANGE,
          rot=(0,math.radians(90),0),parent=ROOT)
for side in (-1,1):
    add_cable(f"BellyCable_{side}",[(-0.70,0.38*side,1.30),(-0.20,0.45*side,1.18),(0.30,0.36*side,1.20),(0.78,0.28*side,1.34)],0.024,M_CABLE,ROOT)

for i,(x,y,z2) in enumerate([(0.24,0.20,2.67),(0.02,-0.20,2.56),(-0.35,0.05,2.48)]):
    add_cyl_between(f"Antenna_{i}",(x,y,2.12),(x-0.08,y,z2),0.018,M_DARK,8,ROOT)

add_empty("WP_SENSOR",(1.96,0,1.46),0.16,ROOT)
add_empty("WP_JUMP_L",(-0.97,0.55,1.68),0.18,ROOT)
add_empty("WP_JUMP_R",(-0.97,-0.55,1.68),0.18,ROOT)
add_empty("WP_BELLY_CORE",(0.22,0,1.18),0.18,ROOT)
add_empty("WP_FRONT_LEFT_KNEE",(1.52,1.22,1.03),0.15,ROOT)
add_empty("WP_FRONT_RIGHT_KNEE",(1.52,-1.22,1.03),0.15,ROOT)

bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0))
ARM=bpy.context.object
ARM.name="ARM_Leaper_V04"
ARM.show_in_front=True
eb=ARM.data.edit_bones
eb.remove(eb[0])
r=eb.new("root"); r.head=(0,0,0); r.tail=(0,0,0.6)
b=eb.new("body"); b.head=(0,0,0.6); b.tail=(0,0,1.55); b.parent=r
h=eb.new("head"); h.head=(0.85,0,1.50); h.tail=(1.85,0,1.43); h.parent=b
for name,hip,knee,ankle,toe in legs:
    u=eb.new(f"{name}_upper"); u.head=hip; u.tail=knee; u.parent=b
    l=eb.new(f"{name}_lower"); l.head=knee; l.tail=ankle; l.parent=u
    f=eb.new(f"{name}_foot"); f.head=ankle; f.tail=toe; f.parent=l
bpy.ops.object.mode_set(mode='OBJECT')
ARM.parent=ROOT
ARM.hide_viewport=True

bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=0.22,depth=1.42,location=(3.60,0,0.78))
P=bpy.context.object
P.name="PlayerScale_1p8m"
P.data.materials.append(M_BLUE)
add_sphere("PlayerScale_Head",(3.60,0,1.60),0.20,M_BLUE,16,8)

M_GROUND=make_mat("M_Ground",(0.055,0.048,0.04),0.0,0.95)
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=3.15,depth=0.04,location=(0,0,0.02))
G=bpy.context.object
G.name="Ground_Plate"
G.data.materials.append(M_GROUND)

ROOT["EnemyType"]="Leaper"
ROOT["PrototypeVersion"]="0.4"
ROOT["TargetPlatform"]="Android"
ROOT["GameplayWeakPoints"]="sensor, left/right jump actuator, belly core, front knee joints"
ROOT["DesignIntent"]="ambush pounce robot with destructible mobility systems"

bpy.ops.object.select_all(action='DESELECT')
ROOT.select_set(True)
bpy.context.view_layer.objects.active=ROOT
print("AFTERFALL Leaper V0.4 generated successfully.")