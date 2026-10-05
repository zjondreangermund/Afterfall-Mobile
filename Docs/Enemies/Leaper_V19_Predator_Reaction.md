# Leaper V1.9 — wide predator reaction and head tracking

V1.9 is the next facial pass after the centered V1.8 face. It is split into a
Blender preview/export update and an Unreal runtime response:

- Blender: `Tools/Blender/afterfall_leaper_v19_predator_reaction_motion.py`
- Unreal: `AAFLeaperEnemy` sight, hearing, and head-turn code

The V1.8 `.blend` must already be applied. V1.9 preserves the centered face,
the `cover_eye` weak-point assembly, the V1.8 neutral transform, and existing
body/leg actions.

## Blender update

1. Open the saved V1.8 `.blend` in Blender.
2. Switch to **Object Mode**.
3. In **Scripting → Text → Open**, select
   `afterfall_leaper_v19_predator_reaction_motion.py` and run it.
4. Put the mouse over the **3D Viewport** and press **Space**.
5. Use **Save As**, then export the updated rig and animation.

The V1.9 NLA track keeps the V1.8 track below it for the corrected neutral
translation and replaces only facial rotation channels. The reaction loop is
short and sharp:

| Control | V1.8 flare | V1.9 flare |
| --- | ---: | ---: |
| Upper mandibles | about 22° | about 58° |
| Lower mandibles | about 30° | about 78° |
| Sensor aim yaw | about ±2.5° | about ±58° |

The large opening is a threat/impact pose, with a quick left-right sensor scan,
short hold, and recoil back to neutral. Run V1.9 again to replace its own track;
it does not duplicate the mandibles or source meshes.

For FBX facial export, temporarily choose `Leaper_V19_PredatorReaction` as the
active action, mute the V1.8 and V1.9 NLA tracks, enable **Bake Animation**, turn
off **All Actions** and **NLA Strips**, and turn off **Add Leaf Bones**. Restore
the active action and unmute the tracks after export. Keep the `face_aim_v18`,
`cover_eye`, and `cover_eye_mandible_*` bones in the selected export.

## Unreal sensing and head turn

`AAFLeaperEnemy` now ticks while alive. Every `SightScanInterval` it checks the
player pawn within `PlayerSightRange` with a visibility trace from the `head`
bone. A visible player calls `NotifyPlayerSeen` and moves the state from
Scanning to Alert.

`AAFCharacter::FirePrimary` reports the shot location to every Leaper in the
world. The Leaper applies `GunshotHearingRange` and remembers that location for
`HearingMemoryDuration`. Damage hits also report their impact/causer location,
so a projectile or hitscan hit produces the same snap response.

The head rotates toward the visible player first, then the last heard location,
and finally eases back to a forward scanning pose. The default limits are 78°
left/right and 32° up/down. The exposed `HeadYawSign` and `HeadPitchSign`
properties handle an imported rig whose local head axes point the opposite way.
Useful tuning properties are exposed under
**Afterfall → Leaper → Alert → Sensing**:

- `PlayerSightRange` 2600 cm, `GunshotHearingRange` 3200 cm
- `VisualMemoryDuration` 1.25 s, `HearingMemoryDuration` 3.5 s
- `HeadTurnSpeed` 5.5, `ThreatHeadTurnSpeed` 13.0
- `MaxHeadYaw` 78°, `MaxHeadPitch` 32°

Blueprint AI or an alternate weapon can call `NotifyPlayerSeen`,
`NotifyGunshotHeard`, or `NotifyThreatSensed` directly. The existing signal
materials remain scanning white, alert yellow, and attacking red.

## Validation

Run the Blender regression checks with Blender 5.2.2 LTS:

```sh
blender --background --factory-startup --python Tools/Blender/tests/test_leaper_v19_motion.py
```

The V1.9 fixture verifies the wider peaks, mirrored jaws, loop closure, track
replacement on rerun, and preservation of the V1.8 body/leg rig. The preview
renderer writes `Docs/Enemies/Images/Leaper_V19_Neutral.jpg` and
`Docs/Enemies/Images/Leaper_V19_Threat.jpg`.
