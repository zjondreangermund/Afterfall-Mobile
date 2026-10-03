# Leaper V1.6 — Pounce Predator

This is the locked visual direction for the standard Leaper enemy.

## Blender source pass

Run `Tools/Blender/afterfall_leaper_v16_pounce_predator.py` on top of the current V1.5 model.

The patch:
- lowers the center of mass and creates a crouched predator idle action;
- pushes the head/eye lower and forward;
- uses long front reach and compressed rear pounce legs;
- slightly restores body mass from V1.5 without returning to the bulky older silhouette;
- covers exposed round joints with angular black armor;
- replaces blocky scanner lights with a thin hostile white sensor slit;
- keeps weak-point covers matte grey while dormant.

The action created by the patch is:

`Leaper_V16_PredatorIdle`

The patch intentionally does **not** apply the pose as the armature rest pose. Review the silhouette first, then lock the approved stance before final FBX export.

## Gameplay visual rules

### AI state light
- Scanning: white
- Alert: yellow
- Attacking / pounce committed: red

Material names already expected by the runtime:
- `LEAP_SIGNAL_Scan_White`
- `LEAP_SIGNAL_Alert_Yellow`
- `LEAP_SIGNAL_Attack_Red`

### Weak points
Weak points are not bright targets before discovery.

- Dormant: matte grey / dark metal
- First successful hit: reveal as pale whitish-yellow
- Subsequent hit: short white-yellow flash
- Destroyed: cover armor is removed and loot is spawned

Current weak-point runtime IDs:
- Eye
- FrontLeft
- FrontRight
- RearLeft
- RearRight

## Armor break / loot

`AAFLeaperEnemy` already hides the matching cover bone when a weak point breaks and spawns the configured loot pickup. Blueprint/VFX can use `OnWeakPointBroken` for sparks, physical debris, sound and a visible detachable plate.

## Target silhouette

The enemy should read as a machine predator rather than a spider toy:

- compact armored core;
- head suspended below the body;
- low crouch;
- long forward reach;
- wide compressed rear stance;
- minimal exposed round joints;
- sharp spike feet;
- one clear hostile sensor focal point.

Do not return to loose glowing rings around the leg joints.
