"""Render the real V1.7 head on the synthetic final-rig fixture.

blender --background --factory-startup --python Tools/Blender/tests/render_leaper_v17_preview.py
Writes two JPEGs under Docs/Enemies/Images; does not load or save artist scenes.
"""
import importlib.util
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('face_fixture', HERE/'test_leaper_v17_face.py')
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)
root, rig = fixture_module.fixture()
parts = fixture_module.face.apply_face()
rig.data.pose_position = 'REST'
for o in bpy.context.scene.objects:
    if o.type == 'MESH' and o not in parts:
        o.hide_render = True

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 88
scene.world = bpy.data.worlds.new('PreviewWorld')
scene.world.use_nodes = True
background = scene.world.node_tree.nodes.get('Background')
background.inputs['Color'].default_value = (0.08,0.10,0.14,1)
background.inputs['Strength'].default_value = 0.40
scene.view_settings.view_transform = 'AgX'
target = Vector((0.62,0,2.025))

def point_at(o, target):
    o.rotation_euler = (target-o.location).to_track_quat('-Z','Y').to_euler()

for name, location, power, color, size in (
    ('Key', (2.9,-2.0,4.2), 1000, (0.74,0.84,1.0), 2.1),
    ('Fill', (2.2,2.8,2.8), 850, (0.90,0.94,1.0), 1.5),
    ('Rim', (-1.2,0.5,3.5), 1300, (1.0,0.59,0.31), 1.4),
    ('Lower', (2.0,-0.2,0.6), 160, (0.55,0.67,1.0), 1.1),
):
    data = bpy.data.lights.new('Preview'+name, 'AREA')
    data.energy, data.color, data.shape, data.size = power, color, 'DISK', size
    o = bpy.data.objects.new('Preview'+name, data)
    scene.collection.objects.link(o)
    o.location = location
    point_at(o, target)

camera_data = bpy.data.cameras.new('PreviewCamera')
camera = bpy.data.objects.new('PreviewCamera', camera_data)
scene.collection.objects.link(camera)
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 1.0
scene.camera = camera
output = HERE.parents[2]/'Docs'/'Enemies'/'Images'
output.mkdir(parents=True, exist_ok=True)
for label, location in (('Front', (4.5,0,2.06)), ('ThreeQuarter', (3.4,-2.7,3.0))):
    camera.location = location
    point_at(camera, target)
    scene.render.filepath = str(output/('Leaper_V17_'+label+'.jpg'))
    bpy.ops.render.render(write_still=True)
    print('Rendered:', scene.render.filepath)
