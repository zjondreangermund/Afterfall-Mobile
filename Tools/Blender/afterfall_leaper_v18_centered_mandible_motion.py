"""Afterfall Leaper V1.8 — centre the V1.7 face and animate its mandibles.

Run this standalone file on the existing V1.7 .blend in Object Mode. No other
Python files are required. Press Space over the 3D viewport to see the loop.
The approved meshes are retained; body/leg actions are not replaced.
"""
import math

ROOT_NAME = "LEAPER_ROOT"
RIG_NAME = "ARM_Leaper_Final"
PASS_KEY = "AfterfallMotionPass"
VERSION = "1.8"
AIM_BONE = "face_aim_v18"
ACTION_NAME = "Leaper_V18_FaceMotion"
TRACK_NAME = "Leaper V1.8 — Face Motion"

# Small adjustments in units of the existing face radius. These are applied
# from stored V1.7 source coordinates, so running twice never doubles a tweak.
FACE_LIFT = 0.10
FACE_TUCK = 0.06
SIDE_TRIM = 0.0
MOTION_STRENGTH = 1.0
LOOP_SECONDS = 4.0

MANDIBLES = {
    "V17_UpperMandible_L": ("cover_eye_mandible_upper_L", -1, "upper"),
    "V17_UpperMandible_R": ("cover_eye_mandible_upper_R", 1, "upper"),
    "V17_LowerMandible_L": ("cover_eye_mandible_lower_L", -1, "lower"),
    "V17_LowerMandible_R": ("cover_eye_mandible_lower_R", 1, "lower"),
}


def body_frame(rig, body_center, previous_forward):
    """Use paired leg roots for the midline, not the old eye's lateral offset."""
    from mathutils import Vector
    up = Vector((0,0,1))
    pairs = []
    for left, right in (("FL_upper", "FR_upper"), ("RL_upper", "RR_upper")):
        a, b = rig.data.bones.get(left), rig.data.bones.get(right)
        if a and b:
            pairs.append(((a.head_local+b.head_local)*0.5, a.head_local-b.head_local))
    if len(pairs) == 2:
        forward = pairs[0][0]-pairs[1][0]
    elif pairs:
        forward = pairs[0][1].cross(up)
    else:
        forward = Vector((1,0,0))  # Final Leaper generators use +X forward.
    forward.z = 0
    if forward.length < 1e-6:
        forward = Vector((1,0,0))
    forward.normalize()
    if forward.dot(previous_forward) < 0:
        forward.negate()
    side = up.cross(forward).normalized()
    center = sum((p[0] for p in pairs), Vector())/len(pairs) if pairs else body_center.copy()
    return center, forward, side, up


def create_motion_action(rig, duration, aim_neutral):
    """Build a Blender 5 layered action without assigning over the active one."""
    import bpy
    action = bpy.data.actions.new(ACTION_NAME)
    action[PASS_KEY] = VERSION
    slot = action.slots.new(id_type='OBJECT', name=rig.name)
    layer = action.layers.new("Mandibles and sensor aim")
    strip = layer.strips.new(type='KEYFRAME')
    channelbag = strip.channelbag(slot, ensure=True)

    # Idle flex, a short threat flare, then return to the EXACT initial pose.
    times = (0.0, 0.18, 0.36, 0.49, 0.59, 0.69, 0.82, 1.0)
    upper_angles = (0, 5, 1, 7, 22, 22, 3, 0)
    lower_angles = (0, 8, 2, 4, 30, 30, 5, 0)
    aim_angles = (0, -2.5, 0, 2.5, 1.0, -1.0, 0, 0)

    def curve(bone_name, index, values, channel='rotation_euler'):
        path = 'pose.bones["'+bone_name+'"].'+channel
        fc = channelbag.fcurves.new(data_path=path, index=index)
        for t, value in zip(times, values):
            key = fc.keyframe_points.insert(1+round(duration*t), value)
            key.interpolation = 'BEZIER'
            key.handle_left_type = 'AUTO_CLAMPED'
            key.handle_right_type = 'AUTO_CLAMPED'
        fc.update()

    for bone_name, sign, level in MANDIBLES.values():
        # Local Y points forward; mirrored rotations open both sides outward.
        angles = upper_angles if level == "upper" else lower_angles
        for i in range(3):
            curve(bone_name, i, [math.radians(sign*a)*MOTION_STRENGTH if i == 1 else 0 for a in angles])
    neutral_location, neutral_rotation, neutral_scale = aim_neutral.decompose()
    neutral_euler = neutral_rotation.to_euler('XYZ')
    for i in range(3):
        angles = aim_angles if i == 2 else [0]*len(times)
        curve(AIM_BONE, i, [neutral_euler[i]+math.radians(a)*MOTION_STRENGTH for a in angles])
        curve(AIM_BONE, i, [neutral_location[i]]*len(times), 'location')
        curve(AIM_BONE, i, [neutral_scale[i]]*len(times), 'scale')
    action.use_fake_user = True
    action.use_frame_range = True
    action.frame_start, action.frame_end = 1, 1+duration
    action.use_cyclic = True
    return action, slot


def apply_motion():
    import bpy
    from mathutils import Matrix, Vector

    root, rig = bpy.data.objects.get(ROOT_NAME), bpy.data.objects.get(RIG_NAME)
    if not root or not rig or rig.type != 'ARMATURE':
        raise RuntimeError("Open your final Leaper .blend with LEAPER_ROOT and ARM_Leaper_Final.")
    if bpy.context.mode != 'OBJECT':
        raise RuntimeError("Switch to Object Mode, then run the V1.8 script again.")
    missing = {"head", "weak_eye", "cover_eye"}-set(rig.data.bones.keys())
    if missing:
        raise RuntimeError("The final weak-point rig is missing: "+", ".join(sorted(missing)))
    if rig.animation_data and rig.animation_data.use_tweak_mode:
        raise RuntimeError("Exit NLA Tweak Mode before applying the face update.")

    parts = [o for o in bpy.data.objects if o.type == 'MESH'
             and o.get("AfterfallFacePass") == "1.7" and o.parent == rig]
    by_name = {o.name: o for o in parts}
    required = set(MANDIBLES) | {"V17_SensorSocket", "V17_WP_Eye_Keel"}
    if not required <= set(by_name):
        raise RuntimeError("Run the V1.7 face script first, then this V1.8 update on the same scene.")
    for name in (AIM_BONE, *(v[0] for v in MANDIBLES.values())):
        existing = rig.data.bones.get(name)
        if existing and existing.get(PASS_KEY) != VERSION:
            raise RuntimeError("A different rig part already uses the bone name "+name)

    scene, view_layer = bpy.context.scene, bpy.context.view_layer
    saved_pose = rig.data.pose_position
    saved_active = view_layer.objects.active
    saved_selected = list(bpy.context.selected_objects)
    saved_hidden = rig.hide_get(), rig.hide_viewport, rig.hide_select
    saved_frame = scene.frame_current
    radius = float(root.get("V17_FaceRadius", 0.25))
    if radius <= 0:
        raise RuntimeError("The V1.7 face radius must be positive.")
    backups = []
    source_points = {}
    completed = False
    try:
        rig.hide_viewport, rig.hide_select = False, False
        rig.hide_set(False)
        rig.data.pose_position = 'REST'
        view_layer.update()
        rig_inverse = rig.matrix_world.inverted()
        for o in parts:
            source_name = o.get("V18_SourceMesh")
            source = bpy.data.meshes.get(source_name) if source_name else None
            if source_name and source is None:
                raise RuntimeError("Stored V1.7 source mesh is missing for "+o.name)
            if source is None:
                source = o.data.copy()
                source.name = o.name+"_V18_Source"
                source.use_fake_user = True
                o["V18_SourceMesh"] = source.name
                matrix = rig_inverse @ o.matrix_world
                o["V18_SourceMatrix"] = [value for row in matrix for value in row]
            values = list(o["V18_SourceMatrix"])
            matrix = Matrix([values[i:i+4] for i in range(0,16,4)])
            source_points[o.name] = [matrix @ v.co for v in source.vertices]

        # The V1.7 socket consists of two 24-vertex rings. Reading their axis
        # recovers the old face direction even when its old eye was off-center.
        points = source_points["V17_SensorSocket"]
        if len(points) != 48:
            raise RuntimeError("The V1.7 sensor topology has been edited; restore its source before running V1.8.")
        back = sum(points[:24], Vector())/24
        front = sum(points[24:], Vector())/24
        old_forward = (front-back).normalized()
        old_up = Vector((0,0,1))
        old_side = old_up.cross(old_forward).normalized()
        old_anchor = (back+front)*0.5 + old_forward*(0.335*radius)
        body = bpy.data.objects.get("Core_Body")
        if body and body.type == 'MESH':
            body_matrix = rig_inverse @ body.matrix_world
            body_center = sum((body_matrix @ Vector(p) for p in body.bound_box), Vector())/8
        else:
            body_center = rig.data.bones["head"].head_local.copy()
        center, forward, side, up = body_frame(rig, body_center, old_forward)
        lateral_offset = (old_anchor-center).dot(side)
        anchor = (old_anchor-side*lateral_offset - forward*(FACE_TUCK*radius)
                  + up*(FACE_LIFT*radius) + side*(SIDE_TRIM*radius))

        # Use the ORIGINAL mesh each time. Action frame and current jaw pose
        # have no influence on the next run's centering or shape.
        for o in parts:
            backups.append((o, [v.co.copy() for v in o.data.vertices], o.matrix_basis.copy()))
            transformed = []
            for p in source_points[o.name]:
                d = p-old_anchor
                transformed.append(anchor + forward*d.dot(old_forward)
                                   + side*d.dot(old_side) + up*d.dot(old_up))
            for v, co in zip(o.data.vertices, transformed):
                v.co = co
            o.data.update()
            o.matrix_parent_inverse = Matrix.Identity(4)
            o.matrix_basis = Matrix.Identity(4)

        for o in saved_selected:
            o.select_set(False)
        rig.select_set(True)
        view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='EDIT')
        bones = rig.data.edit_bones
        aim = bones.get(AIM_BONE) or bones.new(AIM_BONE)
        aim.head = anchor-forward*(1.35*radius)+up*(0.45*radius)
        aim.tail = aim.head+forward*(0.55*radius)
        aim.align_roll(up)
        aim.parent = bones['head']
        aim.use_connect, aim.use_deform = False, True

        # Recenter the existing hit/cover anchors with the sensor; the hit bone
        # names and material slots stay compatible with the Unreal enemy code.
        for name in ('weak_eye', 'cover_eye'):
            b = bones[name]
            delta = anchor-forward*(0.16*radius)-b.head
            b.head += delta
            b.tail += delta
            b.parent = aim
            b.use_connect = False
        for mesh_name, (bone_name, _, _) in MANDIBLES.items():
            o = by_name[mesh_name]
            b = bones.get(bone_name) or bones.new(bone_name)
            b.head = sum((v.co for v in o.data.vertices[:6]), Vector())/6
            b.tail = b.head+forward*(0.40*radius)
            b.align_roll(up)
            b.parent = bones['cover_eye']
            b.use_connect, b.use_deform = False, True
        bpy.ops.object.mode_set(mode='OBJECT')
        for name in (AIM_BONE, *(v[0] for v in MANDIBLES.values())):
            rig.data.bones[name][PASS_KEY] = VERSION
            rig.pose.bones[name].rotation_mode = 'XYZ'
            rig.pose.bones[name].location = (0,0,0)
            rig.pose.bones[name].rotation_euler = (0,0,0)
            rig.pose.bones[name].scale = (1,1,1)
        for o in parts:
            bone_name = MANDIBLES[o.name][0] if o.name in MANDIBLES else (
                'cover_eye' if o.name == 'V17_WP_Eye_Keel' else AIM_BONE)
            for group in list(o.vertex_groups):
                o.vertex_groups.remove(group)
            group = o.vertex_groups.new(name=bone_name)
            group.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')

        if rig.animation_data is None:
            rig.animation_data_create()
        animation = rig.animation_data
        # Centre the neutral FACE in the existing frame-1 body stance too.
        # Older head actions may include a sideways translation or local-axis
        # roll. Compensate only on our new aim bone; keep those source actions.
        rig.data.pose_position = 'POSE'
        scene.frame_set(1)
        view_layer.update()
        head_deform = rig.pose.bones['head'].matrix @ rig.data.bones['head'].matrix_local.inverted()
        body_deform = (rig.pose.bones['body'].matrix @ rig.data.bones['body'].matrix_local.inverted()
                       if 'body' in rig.data.bones else Matrix.Identity(4))
        aim_rest = rig.data.bones[AIM_BONE].matrix_local
        aim_neutral = aim_rest.inverted() @ head_deform.inverted() @ body_deform @ aim_rest
        duration = max(24, round(LOOP_SECONDS*scene.render.fps/scene.render.fps_base))
        action, slot = create_motion_action(rig, duration, aim_neutral)
        previous_actions = []
        for track in list(animation.nla_tracks):
            if track.name == TRACK_NAME and all(s.action and s.action.get(PASS_KEY) == VERSION for s in track.strips):
                previous_actions.extend(s.action for s in track.strips)
                animation.nla_tracks.remove(track)
        track = animation.nla_tracks.new()
        track.name = TRACK_NAME
        strip = track.strips.new("V1.8 breathing / threat flare", 1, action)
        strip.action_slot = slot
        strip.action_frame_start, strip.action_frame_end = 1, 1+duration
        strip.repeat = 1000
        strip.blend_type = 'REPLACE'
        strip.extrapolation = 'NOTHING'
        # This new track contains ONLY new facial-bone channels. The active
        # action and existing body/leg tracks are never overwritten or muted.
        animation.use_nla = True
        for previous in set(previous_actions):
            if previous.users == 1 and previous.use_fake_user:
                bpy.data.actions.remove(previous)
        action.name = ACTION_NAME
        if "V18_PreviousTimeline" not in root:
            root["V18_PreviousTimeline"] = [saved_frame, scene.frame_start, scene.frame_end,
                                           int(scene.use_preview_range), scene.frame_preview_start,
                                           scene.frame_preview_end]
        scene.use_preview_range = True
        scene.frame_preview_start, scene.frame_preview_end = 1, duration
        root["FaceRefitVersion"] = VERSION
        root["V18_CenterCorrection"] = lateral_offset
        root["V18_AlignedAnchor"] = list(anchor)
        root["V18_BodyForward"] = list(forward)
        root["V18_MotionAction"] = action.name
        root["EyeWeakPoint"] = "cover_eye and child cover_eye_mandible_* bones; LEAP_WP_Eye_Grey."
        completed = True
    except Exception:
        if rig.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for o, coords, basis in backups:
            for v, co in zip(o.data.vertices, coords):
                v.co = co
            o.matrix_basis = basis
            o.data.update()
        raise
    finally:
        rig.data.pose_position = 'POSE' if completed else saved_pose
        for o in list(bpy.context.selected_objects):
            o.select_set(False)
        for o in saved_selected:
            o.select_set(True)
        view_layer.objects.active = saved_active
        rig.hide_set(saved_hidden[0])
        rig.hide_viewport, rig.hide_select = saved_hidden[1:]
        scene.frame_set(1 if completed else saved_frame)
        view_layer.update()

    print("AFTERFALL Leaper V1.8 applied: centered face, four hinged mandibles and sensor aim.")
    print("Put the mouse over the 3D view and press Space. Preview frames 1–"+str(duration)+".")
    print("Face motion is on its own NLA track. Save As before exporting the updated skeleton and animation.")
    return {"parts": parts, "action": action, "duration": duration, "anchor": anchor}


if __name__ == "__main__":
    apply_motion()
