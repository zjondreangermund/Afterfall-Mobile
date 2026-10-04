# Leaper — Pounce Predator with V1.7 alien face

This is the current procedural visual direction for the standard Leaper enemy.

## Blender source pass

Open the existing `Leaper_Standard_Final.blend` (final rig `ARM_Leaper_Final`).
For a scene already using V1.6F, run **only**:

`Tools/Blender/afterfall_leaper_v17_alien_predator_face.py`

The V1.7 pass replaces the visible face. It does not rebuild the body or legs.
Earlier V1.6B–F face passes are historical alternatives, not a required sequence.
For an older final-rig scene, run the V1.3 weak-point pass first if its cover bones
are missing, then V1.6 for the crouched stance if wanted, and V1.7 last.

The alien predator shape uses:

- an elongated, tapered carapace with a raised central ridge;
- swept brows and layered temple gills;
- four hooked, tapering mandibles around an inset circular sensor;
- a pointed lower armor keel and recessed mechanical jaw;
- black/graphite armor, with dormant grey breakable mouthparts.

The previous face passes left original head housings/brows in the scene, which
could dominate the new silhouette. V1.7 hides those original rigid head parts as
well as the V1.6B–F layers, while keeping them recoverable in the Outliner.
Mixed body/head meshes and unrelated scene objects are preserved.

See [V1.7 setup and export](Leaper_V17_Alien_Predator.md) for exact steps.

## Gameplay visual rules

### AI state light

The circular sensor ring is the AI-state indicator, not the weak-point armor.

- Scanning: white
- Alert: yellow
- Attacking / pounce committed: red

Runtime material names remain:

- `LEAP_SIGNAL_Scan_White`
- `LEAP_SIGNAL_Alert_Yellow`
- `LEAP_SIGNAL_Attack_Red`

The Blender file exports the ring in the scanning-white slot so `AAFLeaperEnemy` can swap the material at runtime.

### Face weak point

The Eye weak point is now visually represented by the four integrated mandibles and lower keel around the circular sensor.

- Dormant: matte graphite/grey
- First successful hit: pale whitish-yellow
- Later hit: short white-yellow flash
- Broken: the `cover_eye` armor assembly disappears and loot is spawned

The V1.7 face pieces remain compatible with the existing runtime definition:

- weak bone: `weak_eye`
- cover bone: `cover_eye`
- dormant material slot: `LEAP_WP_Eye_Grey`
- loot item: `LeaperSensorPlate`

The sensor/state ring itself should stay intact when the eye armor breaks.

### Other weak points

Existing runtime weak-point IDs remain unchanged:

- Eye
- FrontLeft
- FrontRight
- RearLeft
- RearRight

## Armor break / loot

`AAFLeaperEnemy` hides the matching cover bone when a weak point breaks and spawns the configured loot pickup.

For the face, the V1.7 four mandibles and eye-armor keel are all skinned to `cover_eye`, so they break away as one gameplay weak-point assembly even though visually they read as several armored plates.

Blueprint/VFX can use `OnWeakPointBroken` for:

- sparks;
- physical debris;
- impact sound;
- a short exposed-core effect;
- the visible lootable armor part.

## Target silhouette

The enemy should read as a machine predator rather than a spider toy:

- compact armored core;
- head tucked below the thorax, with an elongated rear skull;
- long, powerful legs;
- low crouch;
- wide pounce stance;
- sharp spike feet;
- minimal exposed round joints;
- one clear circular sensor focal point under aggressive armor;
- faceted, uneven black armor rather than smooth friendly shapes.

Do not return to loose glowing rings around the leg joints.
