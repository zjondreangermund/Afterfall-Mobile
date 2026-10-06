# Afterfall machine rig combat roster

This pass adds a shared autonomous combat brain for the non-Leaper machine rigs and expands the Leaper into a more predatory hunter.

## Rig 01 — Spider Gunner

C++ class:

`AAFGunnerEnemy`

Recommended Blueprint:

`BP_SpiderGunner`

Role:
- ground suppression / area denial
- patrols NavMesh
- hears player gunshots
- investigates the last known position
- enters combat on visual confirmation
- alternates left/right weapon muzzles
- fires short automatic bursts
- repeatedly changes flank side instead of walking straight at the player

Expected mesh sockets:
- `Muzzle_L`
- `Muzzle_R`

The existing spider-like armed rig should use this class.

## Rig 02 — SKYHOUND gunship

C++ class:

`AAFFlyingGunnerEnemy`

Recommended Blueprint:

`BP_FlyingGunner`

Role:
- agile flying pressure unit
- patrols around its spawn area
- reacts to gunshots
- rises to combat altitude
- circles/strafe-orbits the player
- faces the target while moving
- fires alternating-muzzle bursts
- occasionally reverses orbit direction after a burst

Expected mesh sockets:
- `Muzzle_L`
- `Muzzle_R`

Suggested visual direction:
- compact predatory flying machine
- two articulated gun pods
- exposed mechanical stabilizers
- dark gunmetal armor
- white/yellow/red status lighting shared with the machine family

## Rig 03 — GRAVEDROP bomber

C++ class:

`AAFBomberEnemy`

Recommended Blueprint:

`BP_FlyingBomber`

Role:
- heavy flying area-denial unit
- approaches above the player's predicted movement path
- drops explosive charges rather than copying the gunship attack
- leads moving targets before the release
- breaks away after every bomb
- circles back for another attack run

Expected mesh socket:
- `Bomb_Drop`

Default bomb class:
- `AAFBombProjectile`

Recommended Blueprint child:
- `BP_RigBomb`

The bomb has:
- impact detonation
- backup fuse
- radial damage
- configurable gravity
- a Blueprint explosion event for VFX/audio/decal/shake

## Shared machine rig brain

`AAFRigEnemyBase` provides:
- automatic player sight checks
- gunshot hearing
- last-known-position memory
- Patrol / Investigating / Combat states
- visual-memory falloff
- alert-memory falloff
- Blueprint state-change hooks

The HOUND now broadcasts its gunshot position to both:
- Leapers
- all `AAFRigEnemyBase` machines

This means one shot can wake up several different enemy types in the area.

## Leaper predator upgrade

The Leaper keeps its existing:
- white scanning
- yellow alert/investigation
- red attack
- head-first reaction
- movement-sensitive visual detection
- hearing
- pounce
- weak points
- wall/roof surface crawl

This pass adds:
- alternating flank selection
- side/behind-player attack destinations
- last-seen search offsets rather than always walking directly to the final seen point
- repeated search-angle changes if the player remains hidden
- optional vertical ambush routing
- nearby tagged climbable-wall search during combat
- deliberate movement toward a wall before the existing surface-crawl system takes over

Vertical ambush only runs when:
- `Enable Surface Traversal` is ON
- `Enable Vertical Ambush Routes` is ON
- a nearby valid `LeaperClimbable` wall can be found

This allows the intended sequence:

```text
hear shot
-> stop
-> head turns first
-> raised alert posture
-> investigate
-> confirm player
-> choose direct / side flank / vertical ambush
-> disappear around geometry or climb
-> reacquire from another angle
-> pounce
```

## Unreal setup order

1. Build the C++ project.
2. Create Blueprint children from:
   - `AFGunnerEnemy`
   - `AFFlyingGunnerEnemy`
   - `AFBomberEnemy`
   - `AFBombProjectile`
3. Assign the final skeletal/static meshes.
4. Add the required sockets.
5. Implement Blueprint VFX events:
   - `OnGunnerShot`
   - `OnFlyingGunShot`
   - `OnBombReleased`
   - `OnBombExploded`
6. Place a Nav Mesh Bounds Volume for the Spider Gunner and Leaper.
7. Flying rigs do not depend on NavMesh for their flight.
8. Keep Leaper surface traversal OFF until flat-ground AI and animations are visually stable.
9. Then enable surface traversal and tag selected walls/roofs `LeaperClimbable`.

## First combat test

Place:
- 1 Leaper
- 1 Spider Gunner
- 1 Flying Gunner
- 1 Bomber

Start outside their sight range and fire the HOUND.

Expected:
- nearby machines react to the gunshot
- ground rig investigates
- Leaper turns/searches
- flying rigs approach the threat area
- once the player is visible, each rig uses its own attack style
