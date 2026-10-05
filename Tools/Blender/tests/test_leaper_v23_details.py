"""Real bpy tests on a synthetic final Leaper rig, never the artist's .blend.
blender --background --factory-startup --python Tools/Blender/tests/test_leaper_v23_details.py
Or run using Python with bpy 5.2 installed.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import bpy
from mathutils import Matrix, Vector

HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

base=load('v17_fixture',HERE/'test_leaper_v17_face.py')
detail=load('v23',HERE.parent/'afterfall_leaper_v23_integrated_robot_details.py')


def fixture(transformed=True):
    root,rig=base.fixture(transformed=transformed)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.object.mode_set(mode='EDIT')
    for leg,x,y in (('FL',.30,.55),('FR',.30,-.55),('RL',-.40,.55),('RR',-.40,-.55)):
        sign=1 if y>0 else -1
        points=[Vector((x,y,2.3)),Vector((x+.2,y+sign*.65,2.45)),
                Vector((x+.45,y+sign*.95,.5)),Vector((x+.65,y+sign*1.05,.2))]
        parent=rig.data.edit_bones['body']
        for part,a,b in zip(('upper','lower','foot'),points,points[1:]):
            bone=rig.data.edit_bones.get(leg+'_'+part) or rig.data.edit_bones.new(leg+'_'+part)
            bone.head=a; bone.tail=b; bone.parent=parent; parent=bone
    bpy.ops.object.mode_set(mode='OBJECT')
    for leg in ('FL','FR','RL','RR'):
        for part in ('upper','lower','foot'):
            pb=rig.pose.bones[leg+'_'+part]; pb.rotation_mode='XYZ'
            for frame,angle in ((1,-.10),(15,.45),(30,-.10)):
                pb.rotation_euler.x=angle
                pb.keyframe_insert('rotation_euler',frame=frame)
    # Alternate alert action plus NLA must survive without any edits.
    action=rig.animation_data.action
    alert=action.copy(); alert.name='LEAP_Alert_Predator'
    track=rig.animation_data.nla_tracks.new(); track.name='Existing_HeadMotion'
    strip=track.strips.new('Preserve_HeadMotion',1,alert); track.mute=True
    body=bpy.data.objects['Core_Body']
    shell=bpy.data.materials.new('LEAP_FINAL_GraphiteArmor')
    shell.diffuse_color=(.01,.01,.01,1)
    body.data.materials.append(shell)
    # Same data/material used by unrelated scenery: it must NOT be recolored.
    prop=bpy.data.objects.new('SharedMaterial_Scenery',body.data)
    bpy.context.collection.objects.link(prop)
    for name in ('LEAP_SIGNAL_Scan_White','LEAP_SIGNAL_Alert_Yellow','LEAP_SIGNAL_Attack_Red',
                 'LEAP_WP_Eye_Grey','LEAP_WP_Discovered_PaleYellow','LEAP_WP_Hit_WhiteYellow'):
        mat=bpy.data.materials.new(name); mat.diffuse_color=(.2,.3,.4,1)
        body.data.materials.append(mat)
    # Typical old v22 primitives and a similarly named untagged artist object.
    for name,tag in (('V22_FL_ANKLE_COLLAR',True),('V22_HEATSINK_1',True),('V22_ArtistPart',False)):
        mesh=bpy.data.meshes.new(name); mesh.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)])
        obj=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(obj)
        obj.parent=rig
        if tag: obj[detail.OWNER_KEY]='2.2'
    bpy.context.scene.frame_set(15)
    bpy.context.view_layer.update()
    return root,rig


def evaluated_points(obj):
    obj=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [obj.matrix_world @ v.co for v in obj.data.vertices]


def animation_signature(rig):
    actions=[]
    for action in bpy.data.actions:
        curves=[]
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        curves.append((curve.data_path,curve.array_index,
                                       tuple((tuple(k.co),k.interpolation) for k in curve.keyframe_points)))
        actions.append((action.name,tuple(curves)))
    return (tuple(actions),rig.animation_data.action.as_pointer(),
            rig.animation_data.action_slot.as_pointer(),
            tuple((t.name,t.mute,tuple((s.name,s.action.name,s.frame_start,s.frame_end) for s in t.strips))
                  for t in rig.animation_data.nla_tracks))


class DetailChecks(unittest.TestCase):
    def test_preservation_and_actual_bone_attachment(self):
        root,rig=fixture()
        scene=bpy.context.scene
        signature=animation_signature(rig)
        bones={b.name:(b.matrix_local.copy(),b.parent.name if b.parent else None,b.use_deform) for b in rig.data.bones}
        body=bpy.data.objects['Core_Body']; mesh_id=body.data.as_pointer()
        original=evaluated_points(body)
        weak=[(s.material.name,tuple(s.material.diffuse_color)) for s in body.material_slots][1:]
        result=detail.apply_details()
        self.assertEqual(signature,animation_signature(rig))
        self.assertEqual(scene.frame_current,15)
        self.assertEqual(rig.data.pose_position,'POSE')
        self.assertEqual(mesh_id,body.data.as_pointer())
        self.assertEqual(weak,[(s.material.name,tuple(s.material.diffuse_color)) for s in body.material_slots][1:])
        self.assertEqual(bpy.data.objects['SharedMaterial_Scenery'].material_slots[0].material.name,'LEAP_FINAL_GraphiteArmor')
        for b in rig.data.bones:
            self.assertEqual(bones[b.name],(b.matrix_local,b.parent.name if b.parent else None,b.use_deform))
        for a,b in zip(original,evaluated_points(body)):
            self.assertLess((a-b).length,1e-6)
        self.assertEqual(result['removed'],2)
        self.assertIn('V22_ArtistPart',bpy.data.objects)
        self.assertNotIn('V22_FL_ANKLE_COLLAR',bpy.data.objects)
        self.assertEqual(result['panels'],1)
        triangles=0
        for obj in result['parts']:
            obj.data.calc_loop_triangles(); triangles+=len(obj.data.loop_triangles)
            self.assertEqual(obj.type,'MESH')
            self.assertEqual(len(obj.vertex_groups),1)
        self.assertLess(triangles,16000)
        print('V23 fixture:',len(result['parts']),'objects;',triangles,'triangles')
        for frame in (1,8,15,30):
            scene.frame_set(frame)
            for obj in result['parts']:
                bone=obj.vertex_groups[0].name
                matrix=rig.matrix_world @ rig.pose.bones[bone].matrix @ rig.data.bones[bone].matrix_local.inverted()
                for original,posed in zip(obj.data.vertices,evaluated_points(obj)):
                    self.assertLess((matrix @ original.co-posed).length,3e-5,obj.name)

    def test_rerun_in_different_frame_and_no_orphan_growth(self):
        root,rig=fixture()
        first=detail.apply_details()
        geometry={o.name:tuple(tuple(v.co) for v in o.data.vertices) for o in first['parts']}
        counts=(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.collections),len(bpy.data.materials))
        bpy.context.scene.frame_set(27)
        again=detail.apply_details()
        self.assertEqual(counts,(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.collections),len(bpy.data.materials)))
        self.assertEqual(geometry,{o.name:tuple(tuple(v.co) for v in o.data.vertices) for o in again['parts']})
        self.assertEqual(bpy.context.scene.frame_current,27)

    def test_preflight_and_staging_failure_keep_old_details(self):
        root,rig=fixture()
        before=set(bpy.data.objects.keys())
        original=detail.Builder.segment
        def fail(*args): raise RuntimeError('injected staging failure')
        detail.Builder.segment=fail
        try:
            with self.assertRaisesRegex(RuntimeError,'injected'):
                detail.apply_details()
        finally:
            detail.Builder.segment=original
        self.assertEqual(before,set(bpy.data.objects.keys()))
        self.assertEqual(rig.data.pose_position,'POSE')
        self.assertFalse(any(c.name.endswith('_Staging') for c in bpy.data.collections))
        rig.data.bones['FR_foot'].use_deform=False
        with self.assertRaisesRegex(RuntimeError,'deform bones'):
            detail.apply_details()
        self.assertEqual(before,set(bpy.data.objects.keys()))

    def test_fbx_roundtrip_no_extra_bones_and_animation(self):
        root,rig=fixture(transformed=False)
        result=detail.apply_details()
        bones=set(rig.data.bones.keys())
        bpy.ops.object.select_all(action='DESELECT')
        rig.select_set(True)
        for obj in result['parts']: obj.select_set(True)
        bpy.context.view_layer.objects.active=rig
        bpy.context.scene.frame_start=1; bpy.context.scene.frame_end=30
        with tempfile.TemporaryDirectory() as folder:
            path=str(Path(folder)/'LeaperV23_Fixture.fbx')
            bpy.ops.export_scene.fbx(filepath=path,use_selection=True,object_types={'MESH','ARMATURE'},
                                     add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,
                                     bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.fbx(filepath=path)
        imported=next(o for o in bpy.data.objects if o.type=='ARMATURE')
        self.assertEqual(bones,set(imported.data.bones.keys()))
        self.assertIsNotNone(imported.animation_data.action)
        rail=bpy.data.objects['V23_FL_upper_FrameRail']
        bpy.context.scene.frame_set(1); a=evaluated_points(rail)
        bpy.context.scene.frame_set(15); b=evaluated_points(rail)
        self.assertGreater(max((x-y).length for x,y in zip(a,b)),.05)
        for obj in bpy.data.objects:
            if obj.type=='MESH':
                self.assertTrue(any(m.type=='ARMATURE' and m.object==imported for m in obj.modifiers),obj.name)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DetailChecks))
    if not result.wasSuccessful(): raise SystemExit(1)
