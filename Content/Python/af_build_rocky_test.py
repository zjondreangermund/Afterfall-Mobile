"""Build a compact 250m rocky canyon in the CURRENT Unreal Editor level.

Run from Tools > Execute Python Script with the intended test level open.
Uses built-in engine meshes, so no external downloads or source rebuild.
Never deletes existing actors or changes gameplay classes.
"""
import math
import random
import unreal

PREFIX = "AF_RockyTest_"
SEED = 27182
AREA_HALF_CM = 12500
ROCK_MESH = "/Engine/BasicShapes/Sphere.Sphere"
SLAB_MESH = "/Engine/BasicShapes/Cube.Cube"

def _actors():
    return list(unreal.EditorLevelLibrary.get_all_level_actors())

def _mesh(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        raise RuntimeError("Missing built-in mesh: " + path)
    return asset

def _place(mesh, name, location, scale, rotation=(0, 0, 0)):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation)
    )
    if not actor:
        raise RuntimeError("Could not spawn " + name)
    actor.set_actor_label(PREFIX + name)
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_collision_profile_name("BlockAll")
    component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    return actor

def build():
    existing = [a for a in _actors() if a.get_actor_label().startswith(PREFIX)]
    if existing:
        unreal.log_warning(
            "Afterfall rocky area already exists (%d actors). No duplicates created. "
            "Use a new empty level to generate another test world." % len(existing)
        )
        return
    cube, sphere = _mesh(SLAB_MESH), _mesh(ROCK_MESH)
    rng = random.Random(SEED)

    # Engine's BasicShapes/Cube is 100cm on each axis. One flat 250m floor.
    _place(cube, "01_Ground_250m", (0, 0, -85), (250, 250, 1.7))

    # Two irregular ridges leave a ~55m open central chase corridor.
    # Sphere meshes are stand-ins for actual faceted rock assets. Everything
    # gets simple collision and can be replaced with optimized rock meshes.
    count = 0
    for bank in (-1, 1):
        for ix in range(13):
            x = -11900 + ix * 1920
            for band in range(3):
                y = bank * (4300 + band * 2400 + rng.uniform(-650, 650))
                h = (1.4 + 0.7 * band) * rng.uniform(0.75, 1.4)
                dx = rng.uniform(19, 38)  # 100cm mesh radius dimensions
                dy = rng.uniform(14, 30)
                dz = rng.uniform(10, 23) * h
                z = 40 + dz * 42
                _place(sphere, "Ridge_%03d" % count,
                       (x + rng.uniform(-570, 570), y, z),
                       (dx, dy, dz), (rng.uniform(-10, 10), rng.uniform(0, 180), rng.uniform(-15, 15)))
                count += 1

    # Climb and vault course near the open corridor. Rock forms remain optional;
    # the existing traversal C++ actor can be placed separately.
    for i, (x, y, sx, sy, sz) in enumerate([
        (-6800, -1500, 5.5, 4.0, 2.0),
        (-4000, 1600, 8.0, 3.0, 3.5),
        (-800, -2000, 4.0, 6.0, 5.0),
        (2700, 1850, 7.0, 4.0, 2.2),
        (6200, -1400, 4.5, 4.5, 6.0),
    ]):
        _place(cube, "Traversal_%02d" % (i + 1),
               (x, y, sz * 50), (sx, sy, sz))

    # PlayerStart has a floating arrow visualization in editor. It does not
    # change project game mode or replace existing player/Leaper blueprints.
    if not any(a.is_a(unreal.PlayerStart) for a in _actors()):
        player = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PlayerStart, unreal.Vector(-10400, 0, 180), unreal.Rotator(0, 0, 0))
        if player:
            player.set_actor_label(PREFIX + "PlayerStart")

    unreal.log("Afterfall rocky test world generated: 250x250m, %d rocks, five traversal obstacles." % count)
    unreal.log("Save current level as /Game/Afterfall/Maps/L_Rocky_Test; inspect the terrain in viewport.")
    unreal.log_warning("Placeholder smooth rock geometry only; replace with low-poly rock meshes for final rocky appearance.")

build()
