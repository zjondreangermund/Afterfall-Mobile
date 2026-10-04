# Leaper V1.6 — Pounce Predator

This is the locked visual direction for the standard Leaper enemy.

## Blender source pass

Build the current model in this order:

1. `Tools/Blender/afterfall_leaper_v13_breakable_weakpoints.py`
2. `Tools/Blender/afterfall_leaper_v16_pounce_predator.py`
3. `Tools/Blender/afterfall_leaper_v16d_reference_face.py` ← current approved face

The V1.6D face pass replaces the earlier V1.6B/V1.6C experimental face shell and matches the approved reference:

- low-hanging circular eye/sensor below the chassis;
- sharp split brow and angular cheek armor;
- a broken circular state-light ring around the sensor;
- no friendly camera-lens look;
- no loose glowing weak-point ring;
- integrated U-shaped lower face armor around the eye;
- short lower chin spikes;
- black/graphite armor with dark mechanical internals.

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

The Eye weak point is now visually represented by the integrated lower U-shaped armor pieces around the circular sensor.

- Dormant: matte graphite/grey
- First successful hit: pale whitish-yellow
- Later hit: short white-yellow flash
- Broken: the `cover_eye` armor assembly disappears and loot is spawned

The V1.6D face pieces remain compatible with the existing runtime definition:

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

For the face, the V1.6D left/right/chin eye-armor pieces are all skinned to `cover_eye`, so they break away as one gameplay weak-point assembly even though visually they read as several armored plates.

Blueprint/VFX can use `OnWeakPointBroken` for:

- sparks;
- physical debris;
- impact sound;
- a short exposed-core effect;
- the visible lootable armor part.

## Target silhouette

The enemy should read as a machine predator rather than a spider toy:

- compact armored core;
- head suspended low below the body;
- long, powerful legs;
- low crouch;
- wide pounce stance;
- sharp spike feet;
- minimal exposed round joints;
- one clear circular sensor focal point under aggressive armor;
- faceted, uneven black armor rather than smooth friendly shapes.

Do not return to loose glowing rings around the leg joints.
