import bpy
import math
from pathlib import Path
from mathutils import Vector, Quaternion

# ============================================================
# AFTERFALL - LEAPER PREDATOR ALERT STANCE v21
# Blender 5.2+
#
# Creates a looping alert stance:
# - Leaper stops moving
# - front legs lift/spread in a threatening brace
# - rear legs stay planted and loaded
# - body breathes slowly up/down
# - head / face / eye / weak-point bones are NOT keyed
#
# Unreal owns the head at runtime so it can snap toward sounds,
# scan around the last stimulus, and track the player independently.
#
# Output:
# D:\Afterfall\Leaper_Animations_SAFE_V21\LEAP_Alert_Predator.fbx
# ============================================================

RIG_NAME = "ARM_Leaper_Final"
ACTION_NAME = "LEAP_Alert_Predator"
OUT_DIR = Path(r"D:\Afterfall\Leaper_Animations_SAFE_V21")
OUT_FILE = OUT_DIR / "LEAP_Alert_Predator.fbx"

FPS = 30
START = 1
END = 72

rig = bpy.data.objects.get(RIG_NAME)
if not rig or rig.type != 'ARMATURE':
    raise RuntimeError(f"{RIG_NAME} not found.")

scene = bpy.context.scene
scene.render.fps = FPS
scene.render.fps_base = 1.0

if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

if rig.animation_data is None:
    rig.animation_data_create()

rig.animation_data.action = None
scene.frame_set(1)
bpy.context.view_layer.update()

LEG_PREFIXES = ("FL", "FR", "RL", "RR")
LEG_BONES = [f"{p}_{part}" for p in LEG_PREFIXES for part in ("upper", "lower", "foot")]
MOVE_BONES = ["root", "body"] + LEG_BONES

for name in LEG_BONES:
    if name not in rig.pose.bones:
        raise RuntimeError(f"Required bone missing: {name}")

# Return ONLY locomotion bones to rest basis.
# Head/face/eye/weak-point/armor bones are deliberately untouched.
for name in MOVE_BONES:
    pb = rig.pose.bones.get(name)
    if pb:
        pb.matrix_basis.identity()

bpy.context.view_layer.update()

BASE = {}
for name in MOVE_BONES:
    pb = rig.pose.bones.get(name)
    if not pb:
        continue
    pb.rotation_mode = 'QUATERNION'
    BASE[name] = {
        "loc": pb.location.copy(),
        "rot": pb.rotation_quaternion.copy(),
        "scale": pb.scale.copy(),
    }

def restore(name):
    pb = rig.pose.bones.get(name)
    dat = BASE.get(name)
    if not pb or not dat:
        return
    pb.rotation_mode = 'QUATERNION'
    pb.location = dat["loc"].copy()
    pb.rotation_quaternion = dat["rot"].copy()
    pb.scale = dat["scale"].copy()

def axis_to_local(pb, axis_arm):
    axis = pb.bone.matrix_local.to_3x3().inverted() @ axis_arm
    if axis.length < 1e-8:
        return Vector((1, 0, 0))
    return axis.normalized()

def natural_bend_axis(prefix):
    upper = rig.data.bones[f"{prefix}_upper"]
    lower = rig.data.bones[f"{prefix}_lower"]

    u = (upper.tail_local - upper.head_local).normalized()
    l = (lower.tail_local - lower.head_local).normalized()
    axis = u.cross(l)

    if axis.length < 1e-5:
        axis = u.cross(Vector((0, 0, 1)))
        if axis.length < 1e-5:
            axis = u.cross(Vector((1, 0, 0)))
    axis.normalize()

    test = math.radians(8.0)
    plus = Quaternion(axis, test) @ l
    minus = Quaternion(axis, -test) @ l
    if u.angle(minus) > u.angle(plus):
        axis.negate()

    return axis

AXIS = {p: natural_bend_axis(p) for p in LEG_PREFIXES}

def rotate_from_base(name, axis_arm, degrees):
    pb = rig.pose.bones[name]
    restore(name)
    local_axis = axis_to_local(pb, axis_arm)
    pb.rotation_quaternion = BASE[name]["rot"] @ Quaternion(
        local_axis, math.radians(degrees)
    )

def key(name, frame):
    pb = rig.pose.bones.get(name)
    if not pb:
        return
    pb.keyframe_insert(data_path="location", frame=frame)
    pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)
    pb.keyframe_insert(data_path="scale", frame=frame)

old = bpy.data.actions.get(ACTION_NAME)
if old:
    if rig.animation_data.action == old:
        rig.animation_data.action = None
    bpy.data.actions.remove(old, do_unlink=True)

action = bpy.data.actions.new(ACTION_NAME)
rig.animation_data.action = action
scene.frame_start = START
scene.frame_end = END

FRONT_UPPER = 18.0
FRONT_KNEE = 52.0
FRONT_FOOT = -24.0
REAR_UPPER = -7.0
REAR_KNEE = 35.0
REAR_FOOT = -12.0

frames = (1, 10, 19, 28, 37, 46, 55, 64, 72)

for frame in frames:
    phase = (frame - START) / (END - START)
    breath = math.sin(phase * math.tau)
    secondary = math.sin(phase * math.tau * 2.0)

    restore("root")
    key("root", frame)

    restore("body")
    body = rig.pose.bones.get("body")
    if body:
        body.location = BASE["body"]["loc"] + Vector((
            0.0,
            0.006 * secondary,
            0.020 * breath
        ))
        pitch_axis = axis_to_local(body, Vector((0, 1, 0)))
        roll_axis = axis_to_local(body, Vector((1, 0, 0)))
        q_pitch = Quaternion(pitch_axis, math.radians(-1.8 * breath))
        q_roll = Quaternion(roll_axis, math.radians(0.8 * secondary))
        body.rotation_quaternion = BASE["body"]["rot"] @ q_pitch @ q_roll
        key("body", frame)

    for prefix in ("FL", "FR"):
        pulse = 2.5 * breath
        rotate_from_base(f"{prefix}_upper", AXIS[prefix], FRONT_UPPER + pulse)
        rotate_from_base(f"{prefix}_lower", AXIS[prefix], FRONT_KNEE + 3.0 * breath)
        rotate_from_base(f"{prefix}_foot", AXIS[prefix], FRONT_FOOT - 2.0 * breath)

        key(f"{prefix}_upper", frame)
        key(f"{prefix}_lower", frame)
        key(f"{prefix}_foot", frame)

    for prefix in ("RL", "RR"):
        rotate_from_base(f"{prefix}_upper", AXIS[prefix], REAR_UPPER - 1.5 * breath)
        rotate_from_base(f"{prefix}_lower", AXIS[prefix], REAR_KNEE + 2.0 * breath)
        rotate_from_base(f"{prefix}_foot", AXIS[prefix], REAR_FOOT)

        key(f"{prefix}_upper", frame)
        key(f"{prefix}_lower", frame)
        key(f"{prefix}_foot", frame)

scene.frame_set(START)
first_pose = {
    n: (
        rig.pose.bones[n].location.copy(),
        rig.pose.bones[n].rotation_quaternion.copy(),
        rig.pose.bones[n].scale.copy(),
    )
    for n in MOVE_BONES if n in rig.pose.bones
}
scene.frame_set(END)
for name, (loc, rot, scale) in first_pose.items():
    pb = rig.pose.bones[name]
    pb.location = loc
    pb.rotation_quaternion = rot
    pb.scale = scale
    key(name, END)

scene.frame_set(START)
bpy.context.view_layer.update()

OUT_DIR.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action='DESELECT')
rig.hide_set(False)
rig.hide_viewport = False
rig.select_set(True)
bpy.context.view_layer.objects.active = rig

bpy.ops.export_scene.fbx(
    filepath=str(OUT_FILE),
    use_selection=True,
    object_types={'ARMATURE'},
    global_scale=1.0,
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y',
    use_space_transform=True,
    bake_space_transform=True,
    use_armature_deform_only=False,
    add_leaf_bones=False,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=False,
    bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0,
    path_mode='AUTO'
)

scene.frame_start = START
scene.frame_end = END
scene.frame_set(START)
bpy.context.view_layer.update()

print("")
print("====================================================")
print("AFTERFALL LEAPER PREDATOR ALERT STANCE v21 CREATED")
print("Action:", ACTION_NAME)
print("FBX:", OUT_FILE)
print("Head / face / eye / weak-point / armor bones NOT keyed.")
print("Press SPACEBAR to preview frames 1-72.")
print("====================================================")
