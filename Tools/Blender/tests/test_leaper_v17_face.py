"""Real Blender regression checks; no production .blend is overwritten.

blender --background --factory-startup --python Tools/Blender/tests/test_leaper_v17_face.py
Also runs with Python + the matching bpy wheel. Uses a synthetic final-rig scene,
because Leaper_Standard_Final.blend is an artist-local asset, not in this repo.
"""
import importlib.util
from pathlib import Path
import runpy
import tempfile
import unittest

import bpy
import bmesh
from mathutils import Vector

SCRIPT = Path(__file__).resolve().parents[1] / 'afterfall_leaper_v17_alien_predator_face.py'
SPEC = importlib.util.spec_from_file_location('leaper_v17', SCRIPT)
face = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(face)


def fixture(transformed=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    root = bpy.data.objects.new('LEAPER_ROOT', None)
    bpy.context.collection.objects.link(root)
    arm = bpy.data.armatures.new('FixtureArmature')
    rig = bpy.data.objects.new('ARM_Leaper_Final', arm)
    bpy.context.collection.objects.link(rig)
    rig.parent = root
    if transformed:
        root.location = (3, -4, 0.6)
        root.rotation_euler = (0.2, -0.15, 0.8)
        root.scale = (1.3, 0.9, 1.15)
        rig.location = (0.2, 0.3, 0.4)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, pos, parent in (
        ('body', (0,0,2.3), None), ('head', (0.40,0,2.05), 'body'),
        ('weak_eye', (0.80,0,2.0), 'head'), ('cover_eye', (0.80,0,2.0), 'head'),
        ('FL_upper', (0.15,0.6,2.25), 'body'),
    ):
        b = arm.edit_bones.new(name)
        b.head = pos
        b.tail = Vector(pos) + Vector((0.18,0,0))
        if parent:
            b.parent = arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')

    def mesh(name, center, size, bone, material=None):
        vv, ff = face.loft([(center[0]-size[0], center[1], center[2], size[1], size[2]),
                            (center[0]+size[0], center[1], center[2], size[1], size[2])], 16)
        data = bpy.data.meshes.new(name+'_mesh')
        data.from_pydata(vv, [], ff)
        data.update()
        o = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(o)
        o.parent = rig
        vg = o.vertex_groups.new(name=bone)
        vg.add(list(range(len(vv))), 1, 'REPLACE')
        m = o.modifiers.new('FixtureRig', 'ARMATURE')
        m.object = rig
        if material:
            data.materials.append(material)
        return o

    mesh('Core_Body', (0,0,2.3), (0.57,0.48,0.32), 'body')
    mesh('Eye_Lens', (0.8,0,2.0), (0.04,0.27,0.27), 'head')
    mesh('OriginalRoundHousing', (0.65,0,2.05), (0.20,0.41,0.40), 'head')
    mesh('OriginalBoxBrow', (0.89,0,2.27), (0.19,0.48,0.09), 'head')
    mesh('V16F_Brow_L', (0.8,-0.2,2.2), (0.12,0.15,0.08), 'head')
    mesh('V16_SensorSlit', (0.9,0,2.12), (0.01,0.16,0.01), 'head')
    mesh('WP_Eye_Cover', (0.82,0,2.0), (0.02,0.28,0.28), 'cover_eye')
    mesh('V16_JointArmor_FL_upper', (0.1,0.7,2.15), (0.15,0.15,0.18), 'FL_upper')
    # Mixed body/head meshes cannot be retired wholesale.
    mixed = mesh('Head_JoinedBodyAndHead', (0.0,0,2.4), (0.1,0.1,0.1), 'body')
    g = mixed.vertex_groups.new(name='head')
    g.add([0], 0.5, 'REPLACE')
    prop = mesh('Head_UnrelatedProp', (8,8,0), (0.1,0.1,0.1), 'body')
    prop.parent = None
    prop.modifiers.clear()

    for bone in ('body', 'head'):
        pb = rig.pose.bones[bone]
        pb.rotation_mode = 'XYZ'
        for frame, angle in ((1, -0.12), (30, -0.40)):
            pb.rotation_euler.z = angle
            pb.keyframe_insert('rotation_euler', frame=frame)
    bpy.context.scene.frame_set(11)
    bpy.context.view_layer.update()
    return root, rig


class FaceChecks(unittest.TestCase):
    def test_preflight_is_non_destructive(self):
        root, rig = fixture()
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='EDIT')
        rig.data.edit_bones.remove(rig.data.edit_bones['cover_eye'])
        bpy.ops.object.mode_set(mode='OBJECT')
        before = set(bpy.data.objects.keys())
        with self.assertRaisesRegex(RuntimeError, 'cover_eye'):
            face.apply_face()
        self.assertEqual(before, set(bpy.data.objects.keys()))
        self.assertFalse(bpy.data.objects['OriginalBoxBrow'].hide_render)

    def test_cleanup_rerun_binding_and_geometry(self):
        root, rig = fixture(transformed=True)
        action = rig.animation_data.action
        bone_rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
        untouched = {n: bpy.data.objects[n].data.as_pointer() for n in
                     ('Core_Body','V16_JointArmor_FL_upper','Head_JoinedBodyAndHead','Head_UnrelatedProp')}
        generated = face.apply_face()
        self.assertEqual(rig.data.pose_position, 'POSE')
        self.assertEqual(bpy.context.scene.frame_current, 11)
        self.assertEqual(rig.animation_data.action, action)
        for name, matrix in bone_rest.items():
            self.assertEqual(rig.data.bones[name].matrix_local, matrix)
        for name in ('Eye_Lens','OriginalRoundHousing','OriginalBoxBrow','V16F_Brow_L',
                     'V16_SensorSlit','WP_Eye_Cover'):
            self.assertTrue(bpy.data.objects[name].hide_render, name)
            self.assertTrue(bpy.data.objects[name].hide_viewport, name)
        for name, mesh_id in untouched.items():
            self.assertFalse(bpy.data.objects[name].hide_render, name)
            self.assertEqual(bpy.data.objects[name].data.as_pointer(), mesh_id)

        depsgraph = bpy.context.evaluated_depsgraph_get()
        triangles = 0
        for o in generated:
            self.assertEqual(len(o.vertex_groups), 1)
            bone = o.vertex_groups[0].name
            self.assertIn(bone, ('head','cover_eye'))
            expected = rig.matrix_world @ rig.pose.bones[bone].matrix @ rig.data.bones[bone].matrix_local.inverted()
            evaluated = o.evaluated_get(depsgraph)
            for original, posed in zip(o.data.vertices, evaluated.data.vertices):
                self.assertLess((evaluated.matrix_world @ posed.co - expected @ original.co).length, 2e-5)
            bm = bmesh.new()
            bm.from_mesh(o.data)
            self.assertTrue(all(e.is_manifold for e in bm.edges), o.name)
            self.assertTrue(all(f.calc_area() > 1e-10 for f in bm.faces), o.name)
            self.assertGreater(bm.calc_volume(signed=True), 0, o.name)
            bm.free()
            o.data.calc_loop_triangles()
            triangles += len(o.data.loop_triangles)
        self.assertLess(triangles, 2500)
        before = {o.name: tuple(tuple(v.co) for v in o.data.vertices) for o in generated}
        counts = len(bpy.data.objects), len(bpy.data.meshes)
        repeated = face.apply_face()
        self.assertEqual(counts, (len(bpy.data.objects), len(bpy.data.meshes)))
        self.assertEqual(before, {o.name: tuple(tuple(v.co) for v in o.data.vertices) for o in repeated})
        self.assertTrue(all(not o.name.endswith('.001') for o in repeated))
        print('V1.7 geometry:', len(repeated), 'parts;', triangles, 'triangles')

    def test_cover_break_does_not_remove_sensor_and_feedback_exports(self):
        root, rig = fixture()
        generated = face.apply_face()
        cover = [o for o in generated if o.vertex_groups[0].name == 'cover_eye']
        self.assertEqual(len(cover), 5)
        self.assertTrue(all(o.data.materials[0].name == 'LEAP_WP_Eye_Grey' for o in cover))
        signal = bpy.data.objects['V17_StateLight']
        self.assertEqual(signal.vertex_groups[0].name, 'head')
        self.assertEqual(signal.data.materials[0].name, 'LEAP_SIGNAL_Scan_White')
        self.assertTrue(all(not o.hide_render and not o.hide_viewport for o in generated))
        used = {m.name for o in generated for m in o.data.materials}
        for key in ('alert','attack','discovered','hit'):
            self.assertIn(face.MATERIALS[key][0], used)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        original = [v.co.copy() for v in signal.evaluated_get(depsgraph).data.vertices]
        rig.pose.bones['cover_eye'].scale = (0,0,0)
        bpy.context.view_layer.update()
        for a,b in zip(original, signal.evaluated_get(depsgraph).data.vertices):
            self.assertLess((a-b.co).length, 1e-6)
        for o in cover:
            points = [v.co for v in o.evaluated_get(depsgraph).data.vertices]
            self.assertLess(max((v-points[0]).length for v in points), 1e-5)

    def test_upgrade_from_real_v16f_and_selected_fbx_export(self):
        root, rig = fixture()
        runpy.run_path(str(SCRIPT.with_name('afterfall_leaper_v16f_integrated_predator_face.py')))
        generated = face.apply_face()
        previous = [o for o in bpy.data.objects if o.name.startswith('V16F_')]
        self.assertTrue(previous)
        self.assertTrue(all(o.hide_render and o.hide_viewport for o in previous))
        bpy.ops.object.select_all(action='DESELECT')
        rig.select_set(True)
        for o in generated:
            o.select_set(True)
        bpy.context.view_layer.objects.active = rig
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder)/'Leaper_V17_Fixture.fbx')
            bpy.ops.export_scene.fbx(filepath=path, use_selection=True,
                                     object_types={'MESH','ARMATURE'},
                                     add_leaf_bones=False, bake_anim=False)
            self.assertGreater(Path(path).stat().st_size, 10000)
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.fbx(filepath=path)
            used = {m.name for o in bpy.context.scene.objects if o.type == 'MESH'
                    for m in o.data.materials}
            for key in ('eye','scan','alert','attack','discovered','hit'):
                self.assertIn(face.MATERIALS[key][0], used)
            imported = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
            self.assertEqual(len(imported), 1)
            self.assertTrue(face.FACE_BONES <= set(imported[0].data.bones.keys()))
            self.assertFalse(any(o.name.startswith(('V16F_','Eye_Lens','OriginalBox'))
                                 for o in bpy.context.scene.objects))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FaceChecks))
    if not result.wasSuccessful():
        raise SystemExit(1)
