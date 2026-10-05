# Leaper predator behaviour — white / yellow / red

This pass makes the Leaper behave as a predator rather than a normal chasing AI.

## Runtime states

### White — scanning / stalking
- Crawls around reachable NavMesh points at `ScanningMoveSpeed`.
- Head scans independently while the body moves.
- Distant stationary players are harder to notice.
- Player movement above `MovementDetectionSpeed` triggers suspicion.
- Very close players can still be noticed while stationary.

### Yellow — alert / investigate
- Stops immediately.
- Head snaps toward the last seen/heard stimulus first.
- Whole body waits `AlertBodyTurnDelay` before rotating toward the stimulus.
- Uses the looping angry alert stance: front legs raised, rear legs braced, body breathing.
- Continuous visual confirmation for `TargetConfirmationTime` escalates to red.
- If nothing is found before alert memory expires, it returns to white.

### Red — attacking
- Pursues the confirmed player at `AttackMoveSpeed`.
- Pounces when the player is inside the configured min/max pounce range.
- Pounce uses real Character launch velocity, not animation-only movement.
- After landing it stays red if the player is still tracked; otherwise it falls back to yellow.

## Head control

The runtime head turn is deliberately separate from the Blender locomotion animations.

- White: irregular left/right/up/down scan.
- Yellow: looks toward the heard/last-seen location.
- Red: tracks the visible player.
- Head limits and axis signs remain tunable on the Leaper defaults.

## Blender alert animation

Run:

`Tools/Blender/afterfall_leaper_v21_predator_alert_stance.py`

in the final Leaper Blender scene.

It exports:

`D:\Afterfall\Leaper_Animations_SAFE_V21\LEAP_Alert_Predator.fbx`

The script does **not** key the head, face, eye, weak-point, armor or signal-light bones.

## Unreal setup

Import the animation FBXs using the existing `Leaper_Standard_Final_Skeleton`.

In the Leaper Blueprint defaults, assign:

- **Crawl Animation** → `LEAP_Walk_NATURAL`
- **Alert Stance Animation** → `LEAP_Alert_Predator`
- **Attack Crawl Animation** → use `LEAP_Walk_NATURAL` initially
- **Pounce Animation** → the Leaper pounce sequence when ready

The C++ state machine controls movement and signal state:
- Scanning = white
- Alert = yellow
- Attacking = red

The existing weak-point destruction/loot system remains unchanged.
