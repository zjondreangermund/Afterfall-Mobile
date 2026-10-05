"""Afterfall Leaper V1.9 — stronger predator reaction motion.

Run this standalone file on the V1.8-updated ``.blend`` in Object Mode. It
keeps the V1.8 centreline correction, sensor neutral transform, body/leg
actions, and weak-point bones. Only the facial rotation channels are replaced
by a sharper threat flare: the upper mandibles open to about 58 degrees, the
lower mandibles to about 78 degrees, and the sensor aim snaps across a wider
arc before settling back into a scan.

The runtime Unreal implementation in ``AAFLeaperEnemy`` uses the same head
direction idea for seeing the player and hearing gunshots. Save As before
exporting the updated skeleton/animation.
"""
import math


ROOT_NAME = "LEAPER_ROOT"
RIG_NAME = "ARM_Leaper_Final"
PASS_KEY = "AfterfallMotionPass"
VERSION = "1.9"
AIM_BONE = "face_aim_v18"
ACTION_NAME = "Leaper_V19_PredatorReaction"
TRACK_NAME = "Leaper V1.9 — Predator Reaction"
LOOP_SECONDS = 3.2

MANDIBLES = {
    "V17_UpperMandible_L": ("cover_eye_mandible_upper_L", -1, "upper"),
    "V17_UpperMandible_R": ("cover_eye_mandible_upper_R", 1, "upper"),
    "V17_LowerMandible_L": ("cover_eye_mandible_lower_L", -1, "lower"),
    "V17_LowerMandible_R": ("cover_eye_mandible_lower_R", 1, "lower"),
}


def create_reaction_action(rig, duration):
    """Create only rotation curves; V1.8 supplies the neutral translation."""
    import bpy

    action = bpy.data.actions.new(ACTION_NAME)
    action[PASS_KEY] = VERSION
    slot = action.slots.new(id_type="OBJECT", name=rig.name)
    layer = action.layers.new("Predator reaction flare")
    strip = layer.strips.new(type="KEYFRAME")
    channelbag = strip.channelbag(slot, ensure=True)

    # A fast left-right scan, a held threat flare, then a visible recoil. The
    # final key is exactly the first pose so the cyclic loop has no pop.
    times = (0.0, 0.07, 0.15, 0.26, 0.39, 0.52, 0.66, 0.82, 1.0)
    upper_angles = (0, 18, 2, 44, 58, 58, 28, 5, 0)
    lower_angles = (0, 24, 3, 60, 78, 78, 34, 7, 0)
    aim_yaw = (0, -14, -30, 42, 58, 48, 18, 4, 0)
    aim_pitch = (0, 4, -3, -8, -12, -9, -3, 1, 0)

    def curve(bone_name, index, values):
        path = 'pose.bones["' + bone_name + '"].rotation_euler'
        fcurve = channelbag.fcurves.new(data_path=path, index=index)
        for t, value in zip(times, values):
            key = fcurve.keyframe_points.insert(1 + round(duration * t), value)
            key.interpolation = "BEZIER"
            key.handle_left_type = "AUTO_CLAMPED"
            key.handle_right_type = "AUTO_CLAMPED"
        fcurve.update()

    for bone_name, sign, level in MANDIBLES.values():
        angles = upper_angles if level == "upper" else lower_angles
        curve(
            bone_name,
            1,
            [math.radians(sign * angle) for angle in angles],
        )

    # The V1.8 track remains below this one and continues to provide the
    # carefully computed neutral location/scale compensation. Replacing only
    # rotation curves keeps the corrected face centreline intact.
    curve(AIM_BONE, 0, [math.radians(angle) for angle in aim_pitch])
    curve(AIM_BONE, 2, [math.radians(angle) for angle in aim_yaw])

    action.use_fake_user = True
    action.use_frame_range = True
    action.frame_start, action.frame_end = 1, 1 + duration
    action.use_cyclic = True
    return action, slot


def _remove_previous_reaction(animation):
    import bpy

    previous_actions = []
    for track in list(animation.nla_tracks):
        if track.name != TRACK_NAME:
            continue
        if not all(
            strip.action and strip.action.get(PASS_KEY) == VERSION
            for strip in track.strips
        ):
            raise RuntimeError(
                "A track named " + TRACK_NAME + " belongs to another pass."
            )
        previous_actions.extend(
            strip.action for strip in track.strips if strip.action
        )
        animation.nla_tracks.remove(track)

    for action in set(previous_actions):
        if action.users == 1 and action.use_fake_user:
            bpy.data.actions.remove(action)


def apply_motion():
    import bpy

    root = bpy.data.objects.get(ROOT_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if not root or not rig or rig.type != "ARMATURE":
        raise RuntimeError(
            "Open the V1.8-updated Leaper .blend with LEAPER_ROOT and "
            "ARM_Leaper_Final."
        )
    if bpy.context.mode != "OBJECT":
        raise RuntimeError("Switch to Object Mode, then run the V1.9 script again.")

    required = {
        "head",
        "weak_eye",
        "cover_eye",
        AIM_BONE,
        *(value[0] for value in MANDIBLES.values()),
    }
    missing = required - set(rig.data.bones.keys())
    if missing:
        raise RuntimeError(
            "Run the V1.8 centred-face script first; missing: "
            + ", ".join(sorted(missing))
        )
    if rig.animation_data and rig.animation_data.use_tweak_mode:
        raise RuntimeError("Exit NLA Tweak Mode before applying the V1.9 update.")

    parts = [
        obj
        for obj in bpy.data.objects
        if obj.type == "MESH"
        and obj.get("AfterfallFacePass") == "1.7"
        and obj.parent == rig
    ]
    required_parts = set(MANDIBLES)
    if not required_parts <= {obj.name for obj in parts}:
        raise RuntimeError(
            "The V1.8 face meshes are missing; restore the approved V1.8 scene."
        )

    scene = bpy.context.scene
    view_layer = bpy.context.view_layer
    saved_active = view_layer.objects.active
    saved_selected = list(bpy.context.selected_objects)
    saved_frame = scene.frame_current

    if rig.animation_data is None:
        rig.animation_data_create()
    animation = rig.animation_data
    _remove_previous_reaction(animation)

    duration = max(
        24,
        round(LOOP_SECONDS * scene.render.fps / scene.render.fps_base),
    )
    action, slot = create_reaction_action(rig, duration)
    track = animation.nla_tracks.new()
    track.name = TRACK_NAME
    nla_strip = track.strips.new("V1.9 snap / threat flare", 1, action)
    nla_strip.action_slot = slot
    nla_strip.action_frame_start = 1
    nla_strip.action_frame_end = 1 + duration
    nla_strip.repeat = 1000
    nla_strip.blend_type = "REPLACE"
    nla_strip.extrapolation = "NOTHING"
    animation.use_nla = True

    if "V19_PreviousTimeline" not in root:
        root["V19_PreviousTimeline"] = [
            saved_frame,
            scene.frame_start,
            scene.frame_end,
            int(scene.use_preview_range),
            scene.frame_preview_start,
            scene.frame_preview_end,
        ]
    scene.use_preview_range = True
    scene.frame_preview_start = 1
    scene.frame_preview_end = duration
    root["FaceMotionVersion"] = VERSION
    root["V19_MotionAction"] = action.name
    root["V19_UpperMandiblePeakDegrees"] = 58.0
    root["V19_LowerMandiblePeakDegrees"] = 78.0
    root["V19_AimYawPeakDegrees"] = 58.0
    root["V19_MotionNotes"] = (
        "Fast predator scan and wide threat flare; runtime head look is driven "
        "by AAFLeaperEnemy sensing/hearing events."
    )

    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in saved_selected:
        obj.select_set(True)
    view_layer.objects.active = saved_active
    scene.frame_set(1)
    view_layer.update()

    print(
        "AFTERFALL Leaper V1.9 applied: wide predator reaction, "
        "58° upper / 78° lower mandibles, 58° sensor scan."
    )
    print(
        "Preview frames 1–" + str(duration) + "; save a copy before FBX export."
    )
    return {"action": action, "duration": duration, "parts": parts}


if __name__ == "__main__":
    apply_motion()
