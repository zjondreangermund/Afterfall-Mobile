# Leaper predator behaviour — white / yellow / red

This pass makes the Leaper behave as a predator rather than a normal chasing AI.

## Current priority: flat-ground predator test

Surface/wall traversal is intentionally **disabled by default** for this pass. First prove the Leaper on a simple flat NavMesh:

1. natural patrol crawl
2. independent head scanning
3. player movement detection
4. white -> yellow alert transition
5. raised-leg alert stance
6. turn toward the threat
7. investigate a heard/last-seen location
8. yellow -> red after sustained visual confirmation
9. attack crawl and pounce

Once this loop looks right, re-enable surface traversal and return to buildings.

## Runtime states

### White — scanning / stalking
- Crawls around reachable NavMesh points at `ScanningMoveSpeed`.
- Patrol retargeting is deliberately slower so the Leaper does not change direction every few seconds.
- Head scan values are calculated continuously and exposed to the Animation Blueprint.
- Distant stationary players are harder to notice.
- Player movement above `MovementDetectionSpeed` triggers suspicion.
- Very close players can still be noticed while stationary.

### Yellow — alert / investigate
- Stops immediately.
- Head aim values snap/interpolate toward the last seen/heard stimulus first.
- Whole body waits `AlertBodyTurnDelay` before rotating toward the stimulus.
- Uses the looping angry alert stance: front legs raised, rear legs braced, body breathing.
- Holds that stance for `AlertInvestigateDelay`.
- If the threat was heard/last-seen but is not visible, it then crawls slowly toward the location at `InvestigateMoveSpeed`.
- If the player becomes visible, the Leaper stops investigating and watches them while the confirmation timer runs.
- Continuous visual confirmation for `TargetConfirmationTime` escalates to red.
- If nothing is found before alert memory expires, it returns to white.

### Red — attacking
- Pursues the confirmed player at `AttackMoveSpeed`.
- Pounces when the player is inside the configured min/max pounce range.
- Pounce uses real Character launch velocity, not animation-only movement.
- After landing it stays red if the player is still tracked; otherwise it falls back to yellow.

## Head control — important Unreal setup

Do **not** directly rotate the head bone from the normal Skeletal Mesh Component.

The C++ predator brain now calculates and exposes:

- `GetHeadLookYaw()`
- `GetHeadLookPitch()`
- `GetHeadLookRotation()`

Use these in `ABP_Leaper` with a **Transform (Modify) Bone** node targeting the Leaper head/aim bone after the locomotion pose.

Suggested node settings:

- Bone: the runtime head/aim bone used by the final Leaper skeleton
- Rotation Mode: Add to Existing
- Rotation Space: Bone Space or Component Space depending on the imported bone axes
- Pitch input: `GetHeadLookPitch()`
- Yaw input: `GetHeadLookYaw()`

If the head turns the wrong way, use the existing `HeadYawSign` / `HeadPitchSign` values on `BP_LeaperEnemy` instead of changing the skeleton.

## Animation Blueprint state inputs

The C++ class exposes:

- `GetAlertState()`
- `IsInvestigatingThreat()`
- `GetHeadLookYaw()`
- `GetHeadLookPitch()`

Recommended Animation Blueprint states:

```text
Scanning
  -> LEAP_Walk_NATURAL

AlertPose
  -> LEAP_Alert_Predator

Investigating
  -> LEAP_Walk_NATURAL at slower play rate

Attacking
  -> attack crawl / faster LEAP_Walk_NATURAL

Pounce
  -> pounce animation
```

Use `GetAlertState()` plus `IsInvestigatingThreat()` to select AlertPose versus Investigating.

## Single-node fallback

Until `ABP_Leaper` is connected, the C++ class can still play assigned animation assets directly:

- `CrawlAnimation`
- `AlertStanceAnimation`
- `AttackCrawlAnimation`
- `PounceAnimation`

The fallback also supports separate play rates:

- `ScanningAnimationRate`
- `AlertAnimationRate`
- `InvestigationAnimationRate`
- `AttackAnimationRate`

When the Skeletal Mesh is set to **Use Animation Blueprint**, C++ deliberately leaves the animation graph in control.

## Blender alert animation

Run:

`Tools/Blender/afterfall_leaper_v21_predator_alert_stance.py`

in the final Leaper Blender scene.

It exports:

`D:\Afterfall\Leaper_Animations_SAFE_V21\LEAP_Alert_Predator.fbx`

The script does **not** key the head, face, eye, weak-point, armor or signal-light bones.

## Unreal flat-ground test

Use a simple empty level first.

1. Add a large floor.
2. Add a Nav Mesh Bounds Volume covering the floor.
3. Press **P** and confirm the floor is green.
4. Place `BP_LeaperEnemy`.
5. Make sure **Enable Surface Traversal** is OFF.
6. Make sure **Enable Autonomous Behaviour** is ON.
7. Assign the crawl and alert animations or connect `ABP_Leaper`.
8. For the first walk/alert test, you can temporarily turn **Enable Pounce** OFF.
9. Start far enough away that the Leaper begins in white scanning mode.
10. Walk sideways inside its sight range.
11. It should stop, turn yellow, aim its head at you, raise its body/front legs, then go red after sustained sight.
12. Break line of sight: it should investigate the last-seen position and later return to white if it cannot reacquire you.

## Expected first tuning values

Good starting points:

- Scanning Move Speed: 165
- Investigate Move Speed: 125
- Attack Move Speed: 390
- Patrol Retarget: 4–7 seconds
- Alert Body Turn Delay: 0.28 s
- Alert Investigate Delay: 1.10 s
- Target Confirmation Time: 0.55 s
- Visual Memory: 1.25 s
- Alert Memory: 5.0 s

Tune animation rates before changing movement speeds if the feet visibly slide.

## Signal state

The existing material state remains:

- Scanning = white
- Alert = yellow
- Attacking = red

The existing weak-point destruction/loot system remains unchanged.
