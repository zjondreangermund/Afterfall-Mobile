"""Render the V1.9 neutral and wide predator reaction poses.

blender --background --factory-startup --python Tools/Blender/tests/render_leaper_v19_preview.py
Writes JPEGs under Docs/Enemies/Images and does not load or save artist scenes.
"""
import importlib.util
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture_module = load("v19_fixture", HERE / "test_leaper_v19_motion.py")
v19 = fixture_module.motion
root, rig = fixture_module.base.fixture(offset=0.18)
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.rotation_euler = (0, 0, 0)
    bone.location = (0, 0, 0)
bpy.context.view_layer.update()
fixture_module.base.motion.apply_motion()
result = v19.apply_motion()
parts = result["parts"]

for obj in bpy.context.scene.objects:
    if obj.type == "MESH" and obj not in parts:
        obj.hide_render = True

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 88
scene.world = bpy.data.worlds.new("PreviewWorldV19")
scene.world.use_nodes = True
background = scene.world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (0.08, 0.10, 0.14, 1)
background.inputs["Strength"].default_value = 0.40
scene.view_settings.look = "AgX - Medium High Contrast"
target = Vector((0.62, 0, 2.025))


def point_at(obj, target_point):
    obj.rotation_euler = (target_point - obj.location).to_track_quat("-Z", "Y").to_euler()


for name, location, power, color, size in (
    ("Key", (2.9, -2.0, 4.2), 1000, (0.74, 0.84, 1.0), 2.1),
    ("Fill", (2.2, 2.8, 2.8), 850, (0.90, 0.94, 1.0), 1.5),
    ("Rim", (-1.2, 0.5, 3.5), 1300, (1.0, 0.59, 0.31), 1.4),
    ("Lower", (2.0, -0.2, 0.6), 160, (0.55, 0.67, 1.0), 1.1),
):
    data = bpy.data.lights.new("PreviewV19" + name, "AREA")
    data.energy, data.color, data.shape, data.size = power, color, "DISK", size
    obj = bpy.data.objects.new("PreviewV19" + name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    point_at(obj, target)

camera_data = bpy.data.cameras.new("PreviewCameraV19")
camera = bpy.data.objects.new("PreviewCameraV19", camera_data)
scene.collection.objects.link(camera)
camera_data.type = "ORTHO"
camera_data.ortho_scale = 1.20
scene.camera = camera
output = HERE.parents[2] / "Docs" / "Enemies" / "Images"
output.mkdir(parents=True, exist_ok=True)
camera.location = (3.6, -2.1, 2.85)
point_at(camera, target)

for label, frame in (
    ("Neutral", 1),
    ("Threat", 1 + round(result["duration"] * 0.52)),
):
    scene.frame_set(frame)
    scene.render.filepath = str(output / ("Leaper_V19_" + label + ".jpg"))
    bpy.ops.render.render(write_still=True)
    print("Rendered:", scene.render.filepath)
