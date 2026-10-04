"""Blender 5.2 regression fixture for the V1.7 -> V1.8 face update.

blender --background --factory-startup --python Tools/Blender/tests/test_leaper_v18_motion.py
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load('v17_fixture', HERE/'test_leaper_v17_face.py')
motion = load('v18_motion', HERE.parent/'afterfall_leaper_v18_centered_mandible_motion.py')


def fixture(offset=0.18, transformed=False):
    root, rig = base.fixture(transformed=transformed)
    rig.data.pose_position = 'REST'
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    for name, pos in (('FR_upper', (0.15,-0.6,2.25)),
                      ('RL_upper', (-0.5,0.6,2.25)),
                      ('RR_upper', (-0.5,-0.6,2.25))):
        bone = rig.data.edit_bones.new(name)
        bone.head = pos
        bone.tail = Vector(pos)+Vector((0.18,0,0))
        bone.parent = rig.data.edit_bones['body']
    bpy.ops.object.mode_set(mode='OBJECT')
    eye = bpy.data.objects['Eye_Lens']
    for v in eye.data.vertices:
        v.co.y += offset
    eye.data.update()
    bpy.context.view_layer.update()
    base.face.apply_face()
    rig.data.pose_position = 'POSE'
    bpy.context.scene.frame_set(11)
    bpy.context.view_layer.update()
    return root, rig


def evaluated_points(o):
    dg = bpy.context.evaluated_depsgraph_get()
    e = o.evaluated_get(dg)
    return [e.matrix_world @ v.co for v in e.data.vertices]


class MotionChecks(unittest.TestCase):
    def test_centering_and_rerun_preserve_body_and_actions(self):
        root, rig = fixture(transformed=True)
        original_action = rig.animation_data.action
        original_slot = rig.animation_data.action_slot
        body_rest = rig.data.bones['body'].matrix_local.copy()
        head_rest = rig.data.bones['head'].matrix_local.copy()
        before_body = {}
        for frame in (1,11,25):
            bpy.context.scene.frame_set(frame)
            before_body[frame] = evaluated_points(bpy.data.objects['Core_Body'])
        result = motion.apply_motion()
        self.assertAlmostEqual(result['anchor'].y, 0, places=5)
        self.assertAlmostEqual(root['V18_CenterCorrection'], 0.18, places=5)
        self.assertLess((Vector(root['V18_BodyForward'])-Vector((1,0,0))).length, 1e-5)
        self.assertEqual(rig.animation_data.action, original_action)
        self.assertEqual(rig.animation_data.action_slot, original_slot)
        self.assertEqual(rig.data.bones['body'].matrix_local, body_rest)
        self.assertEqual(rig.data.bones['head'].matrix_local, head_rest)
        # Neutral frame is centered in the visible body pose, even though this
        # fixture's old head action yaws the head away from the body centerline.
        body_deform = rig.pose.bones['body'].matrix @ body_rest.inverted()
        expected_hit = rig.matrix_world @ body_deform @ (
            result['anchor']-Vector(root['V18_BodyForward'])*(0.16*root['V17_FaceRadius']))
        actual_hit = rig.matrix_world @ rig.pose.bones['weak_eye'].head
        self.assertLess((actual_hit-expected_hit).length, 1e-5)
        for frame, expected in before_body.items():
            bpy.context.scene.frame_set(frame)
            for a,b in zip(expected, evaluated_points(bpy.data.objects['Core_Body'])):
                self.assertLess((a-b).length, 1e-5)
        first = {o.name: [tuple(v.co) for v in o.data.vertices] for o in result['parts']}
        counts = (len(bpy.data.objects), len(bpy.data.meshes), len(bpy.data.actions), len(rig.data.bones))
        bpy.context.scene.frame_set(60)
        again = motion.apply_motion()
        self.assertEqual(first, {o.name: [tuple(v.co) for v in o.data.vertices] for o in again['parts']})
        self.assertEqual(counts, (len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.actions),len(rig.data.bones)))
        tracks = [t for t in rig.animation_data.nla_tracks if t.name == motion.TRACK_NAME]
        self.assertEqual(len(tracks), 1)
        self.assertEqual(len(tracks[0].strips), 1)

    def test_mirrored_motion_loop_and_cover_break(self):
        root, rig = fixture()
        result = motion.apply_motion()
        duration = result['duration']
        start_rotations = {}
        for frame in (1, 1+round(duration*0.59), 1+duration):
            bpy.context.scene.frame_set(frame)
            for level in ('upper','lower'):
                left = rig.pose.bones['cover_eye_mandible_'+level+'_L']
                right = rig.pose.bones['cover_eye_mandible_'+level+'_R']
                self.assertAlmostEqual(left.rotation_euler.y, -right.rotation_euler.y, places=5)
                if frame == 1:
                    start_rotations[level] = left.rotation_euler.y
                elif frame == 1+duration:
                    self.assertAlmostEqual(left.rotation_euler.y, start_rotations[level], places=5)
                else:
                    self.assertGreater(abs(left.rotation_euler.y), 0.3)
        bpy.context.scene.frame_set(1+round(duration*0.59))
        signal = bpy.data.objects['V17_StateLight']
        sensor_before = evaluated_points(signal)
        rig.pose.bones['cover_eye'].scale = (0,0,0)
        bpy.context.view_layer.update()
        for a,b in zip(sensor_before,evaluated_points(signal)):
            self.assertLess((a-b).length, 1e-5)
        for name, (bone_name,_,_) in motion.MANDIBLES.items():
            self.assertEqual(rig.data.bones[bone_name].parent.name, 'cover_eye')
            points = evaluated_points(bpy.data.objects[name])
            self.assertLess(max((p-points[0]).length for p in points), 1e-5)
        # The weak-point anchor remains at the sensor center while the head scans.
        rig.pose.bones['cover_eye'].scale = (1,1,1)
        bpy.context.view_layer.update()
        lens = bpy.data.objects['V17_SensorIris']
        center = sum(evaluated_points(lens), Vector())/len(lens.data.vertices)
        hit_center = rig.matrix_world @ rig.pose.bones['weak_eye'].head
        self.assertLess((hit_center-center).length, 0.01)

    def test_missing_face_preflight(self):
        root, rig = base.fixture()
        before = (len(bpy.data.objects),len(bpy.data.meshes),len(rig.data.bones))
        with self.assertRaisesRegex(RuntimeError, 'V1.7'):
            motion.apply_motion()
        self.assertEqual(before, (len(bpy.data.objects),len(bpy.data.meshes),len(rig.data.bones)))

    def test_animated_fbx_roundtrip(self):
        root, rig = fixture()
        result = motion.apply_motion()
        # Export just the face animation as an action, retaining the same rig.
        rig.animation_data.action = result['action']
        rig.animation_data.action_slot = result['action'].slots[0]
        for track in rig.animation_data.nla_tracks:
            track.mute = True
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = 1+result['duration']
        bpy.ops.object.select_all(action='DESELECT')
        rig.select_set(True)
        for o in result['parts']:
            o.select_set(True)
        bpy.context.view_layer.objects.active = rig
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder)/'V18_Motion.fbx')
            bpy.ops.export_scene.fbx(filepath=path, use_selection=True,
                                     object_types={'MESH','ARMATURE'}, add_leaf_bones=False,
                                     bake_anim=True, bake_anim_use_all_actions=False,
                                     bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0)
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.fbx(filepath=path)
            imported = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
            for _,(name,_,_) in motion.MANDIBLES.items():
                self.assertEqual(imported.data.bones[name].parent.name, 'cover_eye')
            self.assertIsNotNone(imported.animation_data.action)
            bone = imported.pose.bones['cover_eye_mandible_upper_R']
            bpy.context.scene.frame_set(1)
            start = bone.matrix.copy()
            bpy.context.scene.frame_set(1+round(result['duration']*0.59))
            self.assertGreater(sum(abs(a-b) for ra,rb in zip(start,bone.matrix) for a,b in zip(ra,rb)), 0.1)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MotionChecks))
    if not result.wasSuccessful():
        raise SystemExit(1)
