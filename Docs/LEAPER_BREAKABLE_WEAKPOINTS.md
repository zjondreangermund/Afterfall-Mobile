# Leaper breakable weak points

This system changes the Standard Leaper from obvious glowing target markers to a discovery-and-break system.

## Visual states

1. **Dormant** — integrated graphite/grey armor; no glow.
2. **Discovered** — first successful hit changes that weak point to a pale warm yellow.
3. **Hit flash** — each later hit briefly flashes a brighter white-yellow.
4. **Broken** — the cover bone is hidden and a loot pickup is spawned.

The bright orange leg rings from the early prototype are intentionally removed from the weak-point language.

## Blender

Base weak-point setup:

`Tools/Blender/afterfall_leaper_v13_breakable_weakpoints.py`

Current face treatment:

`Tools/Blender/afterfall_leaper_v17_alien_predator_face.py`

The V1.7 face uses five integrated breakable pieces:

- `V17_UpperMandible_L` / `V17_UpperMandible_R`
- `V17_LowerMandible_L` / `V17_LowerMandible_R`
- `V17_WP_Eye_Keel`

All five use:

- gameplay cover bone: `cover_eye`
- dormant material slot: `LEAP_WP_Eye_Grey`

This means the face looks like several angular armor plates, but Unreal still treats them as one Eye weak-point assembly.

With the [V1.8 motion patch](Enemies/Leaper_V18_Centered_Motion.md), each mandible
is weighted to a separate `cover_eye_mandible_*` child bone under `cover_eye`.
The lower keel stays on `cover_eye`. The existing bone-prefix hit lookup and
parent cover-bone hiding continue to identify and remove the full Eye assembly.

The circular eye ring is **not** the breakable armor. It is the AI state light:

- scan = white
- alert = yellow
- attack = red

## Gameplay bones

Weak-point bones:

- `weak_eye`
- `weak_front_L`
- `weak_front_R`
- `weak_rear_L`
- `weak_rear_R`

Detachable cover bones:

- `cover_eye`
- `cover_front_L`
- `cover_front_R`
- `cover_rear_L`
- `cover_rear_R`

Dormant-grey material slots:

- `LEAP_WP_Eye_Grey`
- `LEAP_WP_FrontL_Grey`
- `LEAP_WP_FrontR_Grey`
- `LEAP_WP_RearL_Grey`
- `LEAP_WP_RearR_Grey`

Feedback materials:

- `LEAP_WP_Discovered_PaleYellow`
- `LEAP_WP_Hit_WhiteYellow`

State-light materials:

- `LEAP_SIGNAL_Scan_White`
- `LEAP_SIGNAL_Alert_Yellow`
- `LEAP_SIGNAL_Attack_Red`

## Unreal runtime

`AAFLeaperEnemy` owns five trace hitboxes attached to the weak-point bones.

Point damage automatically:

- identifies the weak point;
- applies the weak-point damage multiplier;
- remembers discovery;
- swaps the matching material slot;
- performs a short hit flash;
- tracks weak-point health;
- hides the matching cover bone when broken;
- disables that weak-point hitbox;
- spawns configured loot.

The existing pounce behaviour remains intact.

## Loot

Set `WeakPointLootClass` on the Leaper Blueprint to a Blueprint subclass of `AAFLootPickup` with the desired armor/scrap mesh.

Runtime item IDs include:

- `LeaperSensorPlate`
- `LeaperActuatorPlate`
- `LeaperJumpActuator`

For the face, the loot should visually resemble one of the hooked sensor-armor mandibles from the V1.7 design.

## Mobile notes

The implementation uses simple sphere query hitboxes, material swaps and bone hiding rather than runtime mesh destruction. This keeps the feature practical for the mobile target while still giving strong break/damage feedback.
