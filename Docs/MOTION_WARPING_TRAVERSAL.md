# Motion-warped traversal (UE 5.8)

This change builds on main 802392b (including 031c8b8). It changes the movement
owner, not the player/weapon/aim architecture. Full UE compilation and visual
acceptance need the local UE installation and retargeted content; neither the
engine nor the binary animation/Blueprint assets are in this repository.

## Minimum setup

1. Close Unreal, update the project from main and build **AfterfallMobileEditor,
   Development Editor, Win64** with UE 5.8. Restart the editor (native component
   and reflected property changes should not be installed through Live Coding).
2. Keep `ABP_Afterfall_Rifle` on the player mesh and the **TraversalSlot** node
   immediately before Output Pose, after the final layered blend. This is the
   slot already added in the editor. Keep Root Motion from Montages Only.
3. Play. Unassigned traversal actions automatically get cached runtime montages
   using the existing source sequence properties. No individual montage edits
   are required to try the runtime path.
4. Optional, to save editable montage assets: **Tools > Execute Python Script**,
   choose `Content/Python/af_setup_traversal.py`. This generates eight defaults
   under `/Game/Afterfall/Animations/Traversal_Generated` and assigns missing
   entries in the existing `BP_AFCharacter` defaults. The script preserves the
   AnimGraph, imported sequences and explicit montage overrides. It is safe to
   rerun; existing generated assets are never overwritten. Python/editor scripting
   plugins are enabled for editor targets only.

Alternative without Python: select a placed BP_AFCharacter instance, search its
Details for **Generate Traversal Montages**, and click. Assignments apply to that
instance, not automatically to the spawned player's Blueprint defaults. Prefer
the script for the actual player. Save generated content and your Blueprint in
your local project; this repository currently does not contain those binaries.

To use your manually started `AM_AF_Mantle_Stand`, assign it to **MantleStand** in
`BP_AFCharacter > Class Defaults > Afterfall > Traversal > Montages`. It is not
silently modified, found by approximate name or overwritten. Other actions can
remain automatic. An explicitly assigned invalid montage is rejected and logged.

## Target contract

There is exactly one runtime warp target name: **TraversalTarget**. Its world
position is the destination **capsule feet**, not capsule centre or hand contact.
The capsule half-height is subtracted exactly once from the validated centre.

- Vault/hurdle: feet above the validated floor beyond the obstacle.
- Mantle/climb: feet above the supported top, inset by capsule radius/clearance.
- Catch: feet of the validated hanging capsule, calculated from the measured lip
  and configurable `HangBodyDrop`. This target can be below the lip; that is correct.

Each default montage has one Skew Warp state: translation=true, Ignore Z=false,
rotation=true, Warp to Feet Location=true, provider=None, target=TraversalTarget.
The generated window covers the movement clip; the catch clip is trimmed to
`HangPoseFreezeFraction` and held at its end. Full-body playback uses TraversalSlot.
Authored overrides must follow the same endpoint contract; a window ending early
must enable Subtract Remaining Root Motion or be extended to the montage end.
A hand-contact window cannot simply be pointed at the landing target.

Montages preload once in BeginPlay. Source sequences are duplicated with root
motion enabled and the imported assets remain untouched. Only jump/fall visuals
use the old single-node/in-place `IgnoreRootMotion` path. Vault/mantle/catch/climb
use `Montage_Play`, RootMotionFromMontagesOnly, MotionWarping and CharacterMovement.
Flying mode allows animation Z translation; capsule collision stays enabled.

The earlier three-phase path is now only a conservative clearance preflight.
It never positions the actor. CharacterMovement sweeps the actual root-motion
trajectory, including on slow frames. A clear preflight does not guarantee the
chosen animation clears the obstacle: a blocking trajectory aborts safely instead
of disabling collision or teleporting. Completion checks arrival and floor support.
Interruption, timeout, death, movement/AnimInstance replacement and deleted support
restore movement settings, remove the target and restore the weapon attachment.

## Actions and environment limits

| Situation | Action |
|---|---|
| Low obstacle, enough forward speed | Hurdle |
| Waist-height obstacle, supported landing beyond | Vault walk/run |
| Supported broad top/chest height | Mantle stand/walk/run |
| Above direct mantle limit but reachable | Normal jump, then airborne catch |
| Catch reaches hanging destination | Pause catch montage and hang |
| Space while hanging | Climb montage onto a validated supported top |
| Sideways input while hanging | Swept shimmy, wall/lip recheck, updated climb target |
| Back/S or DropLedge | Drop, fall and regrab cooldown |

No test-course actor, object name, world coordinate or obstacle-specific height is
used to compute targets. Detection uses collision queries and configurable reach,
speed and height thresholds. Short-hurdle probes and first-exposed-top scanning
also allow suitable window sills to be considered. Rocks need a walkable top;
windows must clear the full capsule; arbitrary tiny openings are intentionally
rejected. This is not an unrestricted all-geometry climbing solver.

The imported stand mantle remains the default climb-up source, as before. If its
pose is unsuitable when starting from a hang, assign a full hang-to-top climb
montage to **Climb**. `Climb_Start_2_5` is not assumed to be a full hang-to-top clip
just because its name includes “Climb”. These binaries must be visually checked.

Motion Warping adapts root/body travel. It does **not** independently pin fingers,
solve arm reach, or plant both feet on uneven rocks. World-space left/right ledge
contact estimates are exposed for a future AnimGraph IK pass, but that pass is
not installed by this change. Exact contact timing, an appropriate climb source,
catch body offset and animation suitability over the allowed height range still
need in-editor calibration. Do not claim final hand/foot contact is verified.

HOUND is reattached visibly to `Weapon_Back`, or Manny's `spine_03` when the socket
is absent, using `WeaponSlingOffset`. The exact original attachment, relative
transform, visibility and collision are restored. This is an initial attachment
pose, not an animated sling transition. Tune the socket/offset once for the weapon.
The legacy hide setting is only a fallback on meshes without either attachment.

## Debug and validation

Console `af.Traversal.Debug 1` enables diagnostics; `0` disables. Alternatively
check Draw Traversal Debug on the character. Red=wall, green=lip, blue=landing,
cyan/axes=TraversalTarget. Text reports action, measured height (cm), progress and
last result. It displays the last attempted detection, not an always-running scan.

Standalone regression tests:

```sh
g++ -std=c++17 -ISource/AfterfallMobile/Public Tests/traversal_path_test.cpp -o /tmp/af-path && /tmp/af-path
g++ -std=c++17 -ISource/AfterfallMobile/Public Tests/weapon_state_test.cpp -o /tmp/af-weapon && /tmp/af-weapon
python Tests/check_traversal_contract.py
```

UE automation test after building and importing the source animations:
`Automation RunTests Afterfall.Traversal.MontageGeneration` in Output Log.
It verifies generation, catch trimming, root motion, source preservation and
rejection of conflicting target/Z configuration. Missing imported clips fail the
test; this is not a substitute for movement/collision testing in PIE.

PIE acceptance matrix (not executed in the code-only environment):

- Several heights below/above hurdle, vault and direct mantle thresholds, at walk
  and sprint speeds, plus a broad crate, window with/without headroom and sloped rock.
- Tall reachable ledge: jump, catch, hold, shimmy to both ends, climb, and S/drop.
- Thin ledge, insufficient landing space, steep surface and unsupported landing:
  safely reject; never snap through geometry.
- Move/delete support, add an overhead blocker mid-traversal, interrupt the montage,
  replace the AnimInstance and kill the player: no stuck Flying mode or hidden weapon.
- 15/30/60 fps: no tunnel or final target teleport; inspect actual collision aborts.
- Ordinary jump/fall, ADS, reload/fire and HOUND grip after every completion/drop.
- Generate twice: preserve authored AM_AF_Mantle_Stand, existing overrides and sources.
- Package/cook with generated montages referenced by the player BP; verify the
  retargeted source content is included when relying on runtime defaults.

This retains the project's local prototype input model. It does not add multiplayer
traversal RPCs, authoritative target selection or prediction; those need separate
network implementation before this is used for competitive multiplayer.
