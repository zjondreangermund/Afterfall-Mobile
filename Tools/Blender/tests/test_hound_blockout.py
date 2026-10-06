"""Run with bpy Python: test_hound_blockout.py OUTPUT.blend. Use a new path."""
import bpy, runpy, sys, hashlib, json
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
if len(args)!=1: raise SystemExit('Specify a new OUTPUT.blend path')
target=Path(args[0]).resolve()
if target.exists():raise SystemExit('Output already exists; choose a new path')
source=Path(__file__).resolve().parents[1]/'afterfall_af01_hound_blockout.py'
module=runpy.run_path(str(source))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(location=(4,5,6))
sentinel=bpy.context.object;sentinel.name='TEST_UNRELATED_OBJECT'
frame=bpy.context.scene.frame_current
units=bpy.context.scene.unit_settings.scale_length
def snapshot():
    result={}
    for o in bpy.data.collections['AF01_HOUND'].objects:
        if o.type=='MESH':
            result[o.name]=hashlib.sha256(repr(([tuple(o.matrix_world@v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()
    return result
root=module['build_hound']()
assert len(snapshot())==9
assert 0<root['TriangleCount']<10000
assert all(bpy.data.objects.get('SOCKET_'+n) for n in module['SOCKETS'])
before=snapshot();counts=(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials),len(bpy.data.collections))
root=module['build_hound']()
assert snapshot()==before
assert counts==(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials),len(bpy.data.collections))
assert tuple(sentinel.location)==(4,5,6)
assert bpy.context.scene.frame_current==frame and bpy.context.scene.unit_settings.scale_length==units
assert bpy.context.view_layer.objects.active==sentinel
for name in before:
    o=bpy.data.objects[name]
    assert len(o.data.uv_layers)>0
    assert all(p.area>1e-12 for p in o.data.polygons),name
    assert all(abs(s-1)<1e-6 for s in o.scale),name
report={'blender':bpy.app.version_string,'meshes':len(before),'triangles':root['TriangleCount'],'sockets':list(module['SOCKETS']),'rerun_stable':True,'unrelated_object_preserved':True}
bpy.data.objects.remove(sentinel,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
target.with_suffix('.validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
