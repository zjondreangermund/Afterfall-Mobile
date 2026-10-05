"""Blender 5.2 regression fixture for the V1.8 -> V1.9 reaction pass.

blender --background --factory-startup --python Tools/Blender/tests/test_leaper_v19_motion.py
"""
import importlib.util
from pathlib import Path
import unittest

import bpy

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load("v18_motion_fixture", HERE / "test_leaper_v18_motion.py")
motion = load(
    "v19_motion",
    HERE.parent / "afterfall_leaper_v19_predator_reaction_motion.py",
)


class PredatorReactionChecks(unittest.TestCase):
    def test_wide_reaction_preserves_v18_track_and_centered_rig(self):
        root, rig = base.fixture()
        v18 = base.motion.apply_motion()
        body_rest = rig.data.bones["body"].matrix_local.copy()
        result = motion.apply_motion()

        self.assertEqual(rig.data.bones["body"].matrix_local, body_rest)
        self.assertEqual(root["FaceMotionVersion"], "1.9")
        self.assertEqual(root["V19_UpperMandiblePeakDegrees"], 58.0)
        self.assertEqual(root["V19_LowerMandiblePeakDegrees"], 78.0)
        self.assertEqual(root["V19_AimYawPeakDegrees"], 58.0)
        self.assertEqual(result["duration"], round(3.2 * 24))

        self.assertEqual(
            len(
                [
                    track
                    for track in rig.animation_data.nla_tracks
                    if track.name == base.motion.TRACK_NAME
                ]
            ),
            1,
        )
        self.assertEqual(
            len(
                [
                    track
                    for track in rig.animation_data.nla_tracks
                    if track.name == motion.TRACK_NAME
                ]
            ),
            1,
        )

        peak_frame = 1 + round(result["duration"] * 0.52)
        bpy.context.scene.frame_set(peak_frame)
        upper = rig.pose.bones["cover_eye_mandible_upper_R"].rotation_euler.y
        lower = rig.pose.bones["cover_eye_mandible_lower_R"].rotation_euler.y
        aim = rig.pose.bones[motion.AIM_BONE].rotation_euler.z
        self.assertGreater(abs(upper), 0.85)
        self.assertGreater(abs(lower), 1.15)
        self.assertGreater(abs(aim), 0.75)

        # The cyclic end pose matches the start pose and the mirrored jaws stay
        # opposite around the centred eye sensor.
        bpy.context.scene.frame_set(1)
        start = {
            name: tuple(rig.pose.bones[name].rotation_euler)
            for name, _, _ in motion.MANDIBLES.values()
        }
        bpy.context.scene.frame_set(1 + result["duration"])
        for name, _, _ in motion.MANDIBLES.values():
            self.assertAlmostEqual(
                rig.pose.bones[name].rotation_euler.y,
                start[name][1],
                places=5,
            )
        bpy.context.scene.frame_set(peak_frame)
        self.assertAlmostEqual(
            rig.pose.bones["cover_eye_mandible_upper_L"].rotation_euler.y,
            -rig.pose.bones["cover_eye_mandible_upper_R"].rotation_euler.y,
            places=5,
        )

    def test_rerun_replaces_only_v19_track(self):
        root, rig = base.fixture()
        base.motion.apply_motion()
        first = motion.apply_motion()
        counts = (len(bpy.data.actions), len(rig.animation_data.nla_tracks))
        second = motion.apply_motion()
        self.assertEqual(first["duration"], second["duration"])
        self.assertEqual(counts, (len(bpy.data.actions), len(rig.animation_data.nla_tracks)))
        self.assertEqual(
            len([track for track in rig.animation_data.nla_tracks if track.name == motion.TRACK_NAME]),
            1,
        )


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PredatorReactionChecks)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
