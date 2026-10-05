"""Run with Blender's Python/bpy: test_leaper_v26_scene.py INPUT.blend OUTPUT.blend.

Use a separate output path. Does not overwrite the input scene.
"""
import bpy, runpy, hashlib, json, sys
from pathlib import Path

args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
if len(args) != 2:
    raise SystemExit('Provide INPUT.blend and a separate OUTPUT.blend path')
source, target = map(lambda p: Path(p).resolve(), args)
assert source != target, 'Output must not overwrite the input'
assert not target.exists(), 'Choose a new output file'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
script = Path(__file__).resolve().parents[1]/'afterfall_leaper_v26_fitted_combat_armor.py'
module = runpy.run_path(str(script))
rig = bpy.data.objects['ARM_Leaper_Final']
scene = bpy.context.scene
def digest(v): return hashlib.sha256(repr(v).encode()).hexdigest()
def signature():
    return digest(([(b.name, tuple(tuple(r) for r in b.matrix_local), b.parent.name if b.parent else None) for b in rig.data.bones], [(a.name, [(f.data_path, f.array_index, [(tuple(k.co),tuple(k.handle_left),tuple(k.handle_right),k.interpolation) for k in f.keyframe_points]) for layer in a.layers for strip in layer.strips for bag in strip.channelbags for f in bag.fcurves]) for a in bpy.data.actions], [(t.name,t.mute,[(s.name,s.action.name,s.frame_start,s.frame_end) for s in t.strips]) for t in rig.animation_data.nla_tracks]))
def mesh_signature(o):
    return digest(([(tuple(v.co), [(g.group,g.weight) for g in v.groups]) for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons]))
def protected_slots():
    return {(o.name,i):s.material.name for o in scene.objects if o.type=='MESH' for i,s in enumerate(o.material_slots) if s.material and any(t in s.material.name.lower() for t in module['PROTECTED'])}
protected = protected_slots()
original = {o.name: mesh_signature(o) for o in scene.objects if o.type == 'MESH'}
before = signature()
frame = scene.frame_current
parts = module['apply_armor']()
assert signature() == before
assert scene.frame_current == frame
assert protected == protected_slots()
assert all(mesh_signature(bpy.data.objects[n]) == s for n,s in original.items())
max_error = 0
for f in (1,18,36,54,72):
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    for obj in parts:
        bone = obj.vertex_groups[0].name
        transform = rig.matrix_world @ rig.pose.bones[bone].matrix @ rig.data.bones[bone].matrix_local.inverted()
        evaluated = obj.evaluated_get(dg)
        for a,b in zip(obj.data.vertices,evaluated.data.vertices):
            max_error = max(max_error, (transform @ a.co - evaluated.matrix_world @ b.co).length)
        assert all(p.area > 1e-10 for p in obj.data.polygons), obj.name
assert max_error < 1e-4
shapes = {o.name:mesh_signature(o) for o in parts}
counts = (len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials))
parts = module['apply_armor']()
assert shapes == {o.name:mesh_signature(o) for o in parts}
assert counts == (len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials))
assert signature() == before
assert protected == protected_slots()
scene.frame_set(frame)
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
report = dict(blender=bpy.app.version_string,original_meshes_unchanged=len(original),bones=len(rig.data.bones),actions=[a.name for a in bpy.data.actions],parts=len(parts),frames_checked=[1,18,36,54,72],maximum_attachment_error=max_error,rerun_stable=True)
target.with_suffix('.validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
