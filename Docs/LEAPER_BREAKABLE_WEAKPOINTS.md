# Leaper breakable weak points

This pass changes the Standard Leaper from obvious glowing target markers to a discovery-and-break system.

## Visual states

1. **Dormant** — integrated graphite/grey armor arc; no glow.
2. **Discovered** — first successful hit changes that weak point to a pale warm yellow.
3. **Hit flash** — each later hit briefly flashes a brighter white-yellow.
4. **Broken** — the cover bone is hidden and a loot pickup is spawned.

The bright orange leg rings from the earlier prototype are intentionally removed from the weak-point language.

## Blender

Run:

`Tools/Blender/afterfall_leaper_v13_breakable_weakpoints.py`

on top of `Leaper_Standard_Final.blend`.

It adds these gameplay bones:

- `weak_eye`
- `weak_front_L`
- `weak_front_R`
- `weak_rear_L`
- `weak_rear_R`

and detachable cover bones:

- `cover_eye`
- `cover_front_L`
- `cover_front_R`
- `cover_rear_L`
- `cover_rear_R`

It also creates separate dormant-grey material slots:

- `LEAP_WP_Eye_Grey`
- `LEAP_WP_FrontL_Grey`
- `LEAP_WP_FrontR_Grey`
- `LEAP_WP_RearL_Grey`
- `LEAP_WP_RearR_Grey`

Two tiny internal carrier meshes force the feedback materials into the FBX:

- `LEAP_WP_Discovered_PaleYellow`
- `LEAP_WP_Hit_WhiteYellow`

Re-export the Leaper FBX with Mesh + Armature selected, then reimport the skeletal mesh in Unreal.

## Unreal runtime

`AAFLeaperEnemy` now owns five trace hitboxes attached to the weak-point bones.

Point damage automatically:

- identifies the weak point
- applies the weak-point damage multiplier
- remembers discovery
- swaps the matching material slot
- performs a short hit flash
- tracks weak-point health
- hides the matching cover bone when broken
- disables that weak-point hitbox
- spawns configured loot

The existing pounce behaviour remains intact.

## Loot

Set `WeakPointLootClass` on the Leaper Blueprint to a Blueprint subclass of `AAFLootPickup` that has the desired armor/scrap mesh.

The runtime assigns item IDs such as:

- `LeaperSensorPlate`
- `LeaperActuatorPlate`
- `LeaperJumpActuator`

The spawned pickup can use physics impulse so the broken part visibly drops away from the Leaper before being collected.

## Mobile notes

The implementation uses simple sphere query hitboxes, material swaps and bone hiding rather than runtime mesh destruction. This keeps the feature practical for the Galaxy A15 target while still giving the player strong break/damage feedback.
