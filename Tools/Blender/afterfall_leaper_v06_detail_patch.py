import bpy
import math
from mathutils import Vector

# AFTERFALL - LEAPER V0.6 DETAIL PATCH
# Run on top of the user's manually refined V0.5/V0.4 scene.
# Does NOT clear the scene.
# Adds non-destructive detail parts to improve silhouette and mechanical readability.
# Blender 5.2+

def obj(name):
    return bpy.data.objects.get(name)

def mat(name):
    return bpy.data.materials.get(name)

ROOT = obj("LEAPER_ROOT")
if not ROOT:
    raise RuntimeError("LEAPER_ROOT not found. Open the Leaper V0.4/V0.5 scene first.")

M_ARMOR  = mat("M_Armor_BoneWhite")
M_ARMOR2 = mat("M_Armor_DarkWhite")
M_DARK   = mat("M_Mechanical_Dark")
M_ORANGE = mat("M_Accent_Orange")
M_RED    = mat("M_Sensor_Red")
M_CABLE  = mat("M_Cable")
M_HYD    = mat("M_Hydraulic")

def add_box(name, loc, scale, material, bevel=0.05, rot=(0,0,0)):
    if obj(name):
        return obj(name)
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b = o.modifiers.new("Bevel", "BEVEL")
    b.width = bevel
    b.segments = 3
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=b.name)
    if material:
        o.data.materials.append(material)
    o.parent = ROOT
    return o

def add_cyl_between(name, a, b, radius, material, verts=12):
    if obj(name):
        return obj(name)
    a = Vector(a); b = Vector(b)
    d = b - a
    if d.length < 0.0001:
        return None
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=d.length, location=(a+b)/2)
    o = bpy.context.object
    o.name = name
    o.rotation_mode='QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z','Y')
    if material:
        o.data.materials.append(material)
    o.parent = ROOT
    return o

def add_torus(name, loc, major, minor, material, rot=(0,0,0)):
    if obj(name):
        return obj(name)
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=20, minor_segments=8, location=loc, rotation=rot)
    o=bpy.context.object
    o.name=name
    if material:
        o.data.materials.append(material)
    o.parent=ROOT
    return o

def add_cable(name, points, radius=0.015):
    if obj(name):
        return obj(name)
    curve=bpy.data.curves.new(name+"_Curve", type='CURVE')
    curve.dimensions='3D'
    curve.bevel_depth=radius
    curve.bevel_resolution=2
    sp=curve.splines.new('BEZIER')
    sp.bezier_points.add(len(points)-1)
    for bp,co in zip(sp.bezier_points,points):
        bp.co=co
        bp.handle_left_type='AUTO'
        bp.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,curve)
    bpy.context.collection.objects.link(o)
    if M_CABLE:
        curve.materials.append(M_CABLE)
    o.parent=ROOT
    return o

add_box("V06_CheekGuard_L",(1.80, 0.39,1.42),(0.23,0.11,0.09),M_ARMOR2,0.04,rot=(math.radians(4),math.radians(-14),math.radians(-12)))
add_box("V06_CheekGuard_R",(1.80,-0.39,1.42),(0.23,0.11,0.09),M_ARMOR2,0.04,rot=(math.radians(-4),math.radians(-14),math.radians(12)))
add_box("V06_SensorChin",(1.78,0,1.22),(0.27,0.31,0.055),M_DARK,0.035,rot=(0,math.radians(-7),0))

for side in (-1,1):
    add_box(f"V06_FrontShoulderBlade_{side}",(0.58,0.91*side,1.65),(0.38,0.10,0.13),M_ARMOR,0.045,rot=(math.radians(8*side),math.radians(-11),math.radians(-15*side)))
    add_box(f"V06_RearShoulderBlade_{side}",(-0.62,0.91*side,1.62),(0.35,0.10,0.13),M_ARMOR2,0.045,rot=(math.radians(-6*side),math.radians(12),math.radians(12*side)))

for i,(x,y,z,rz) in enumerate([
    (-0.52, 0.43,2.11,  3),(-0.18, 0.43,2.13,  1),( 0.18, 0.43,2.11, -2),
    (-0.52,-0.43,2.11, -3),(-0.18,-0.43,2.13, -1),( 0.18,-0.43,2.11,  2)]):
    add_box(f"V06_TopScale_{i}",(x,y,z),(0.20,0.16,0.035),M_ARMOR2,0.025,rot=(0,math.radians(-5),math.radians(rz)))

for side in (-1,1):
    add_cyl_between(f"V06_ActuatorGuardA_{side}",(-0.73,0.72*side,1.87),(-1.38,0.84*side,1.25),0.035,M_DARK,10)
    add_cyl_between(f"V06_ActuatorGuardB_{side}",(-0.86,0.77*side,1.98),(-1.48,0.90*side,1.38),0.030,M_DARK,10)
    for j in range(3):
        x=-0.92-(0.18*j)
        add_box(f"V06_JumpFin_{side}_{j}",(x,0.72*side,1.75-(0.12*j)),(0.09,0.16,0.035),M_ORANGE,0.025,rot=(math.radians(6*side),math.radians(15),0))

leg_info = {
    "FL": ((0.78, 0.64,1.54),(1.52, 1.22,1.03),(2.07, 1.82,0.35)),
    "FR": ((0.78,-0.64,1.54),(1.52,-1.22,1.03),(2.07,-1.82,0.35)),
    "ML": ((0.00, 0.78,1.52),(0.18, 1.50,0.91),(0.58, 2.08,0.28)),
    "MR": ((0.00,-0.78,1.52),(0.18,-1.50,0.91),(0.58,-2.08,0.28)),
    "RL": ((-0.82, 0.64,1.54),(-1.43, 1.30,1.02),(-2.06, 1.79,0.33)),
    "RR": ((-0.82,-0.64,1.54),(-1.43,-1.30,1.02),(-2.06,-1.79,0.33)),
}
for name,(hip,knee,ankle) in leg_info.items():
    hv=Vector(hip); kv=Vector(knee); av=Vector(ankle)
    sidev=(Vector((0,0,1)).cross(av-kv))
    if sidev.length: sidev.normalize()
    sidev*=0.055
    add_cyl_between(f"V06_{name}_LowerHydraulic",kv+sidev,av+sidev,0.028,M_HYD,10)
    mid=(kv+av)/2
    plate=add_box(f"V06_{name}_ShinArmor",tuple(mid),(0.22,0.09,0.065),M_ARMOR2,0.035)
    if plate:
        plate.rotation_mode='QUATERNION'
        plate.rotation_quaternion=(av-kv).to_track_quat('X','Z')
    add_cable(f"V06_{name}_Cable",[tuple(hv),tuple((hv+kv)/2 + Vector((0,0,0.08))),tuple(kv),tuple((kv+av)/2 + Vector((0,0,0.05))),tuple(av)],0.013)

for side in (-1,1):
    add_cyl_between(f"V06_BellyRib_{side}",(-0.55,0.34*side,1.27),(0.62,0.30*side,1.25),0.035,M_DARK,10)

for i,(x,z) in enumerate([(-0.70,2.12),(-0.92,2.08),(-1.10,2.00)]):
    add_box(f"V06_RearFin_{i}",(x,0,z),(0.05,0.18,0.16),M_DARK,0.025,rot=(0,math.radians(18),0))

for side in (-1,1):
    add_torus(f"V06_StatusRing_{side}",(0.38,0.82*side,1.55),0.075,0.018,M_ORANGE,rot=(math.radians(90),0,0))

ROOT["DetailPass"]="V0.6"
ROOT["DetailNotes"]="face guards, shoulder blades, actuator guards/fins, leg hydraulics/cables, shin armor, rear fins"

bpy.ops.object.select_all(action='DESELECT')
ROOT.select_set(True)
bpy.context.view_layer.objects.active=ROOT
print("AFTERFALL Leaper V0.6 detail patch applied.")
