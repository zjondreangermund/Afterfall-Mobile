# AF-01 HOUND — Machine-Breaker Rifle

First playable implementation and original procedural art blockout. Built on main
`a70da945dfddf76f4922ffda8c9ff9aceeae701f`. No Leaper source, rig or Blender scripts
were changed. The separate Leaper PRs are not merged or reverted by this branch.

## What changed

`AAFWeaponBase` owns firing, point damage, ammunition, reload, cadence, recoil,
heat, overheat lock, muzzle effects and shot noise. `AAFHoundWeapon` supplies the
AF01_HOUND identity and visible engine-primitive placeholder. Blueprint subclasses
can tune `Tuning` in Class Defaults and assign art/effects without recompilation.

`AAFCharacter` keeps its camera, movement, health and inventory. `FirePrimary()`
still attempts one shot; input press/release now calls StartPrimaryFire and
StopPrimaryFire for automatic fire. It owns one equipped actor reference, default
HOUND spawn, aim FOV and equip/drop operations. Old PrimaryDamage/FireRange
properties are retained as deprecated serialized fields; migrate custom values
to the weapon Tuning. There is one damage path, now in the weapon, not two.

Camera aim first resolves the crosshair target. The actual damage ray originates
at the muzzle, with a pawn-to-muzzle obstruction check to stop firing through
cover. A valid shot consumes one round, creates heat, applies recoil, triggers
effects and notifies existing Leapers even on misses. Empty, overheated, reloading
or rate-limited attempts do none of those things. Point damage retains hit
component and bone information for the Leaper's existing weak-point processing.
The Leaper's separate damage-threat response remains untouched.

## Default tuning (gameplay values, not firearm engineering)

| Property | Default |
|---|---:|
| Magazine / reserve | 30 / 120 |
| Fire rate | 500 rounds/minute, automatic |
| Reload duration | 2.2 seconds |
| Point damage | 25 before the enemy's existing modifiers |
| Effective range | 12,000 Unreal cm (120 m), hard cutoff |
| Hip / aim cone half-angle | 0.8 / 0.15 degrees |
| Pitch / random yaw recoil | 0.35 / ±0.12 degrees per shot |
| Heat per shot / maximum | 8 / 100 |
| Cooldown delay / cooling rate | 0.35 seconds / 18 units per second |
| Resume threshold after overheat | 35 units |

Recoil changes controller aim; the player counters it manually. Heat locks after
13 uninterrupted shots with defaults. Holding the trigger resumes fire after
cooling below the resume threshold. Reload does not reset heat. Reload transfers
only the missing rounds from reserve at completion; cancelling it transfers none.
Reload stops automatic fire: release and press fire again afterward. Fire cadence
is capped at one shot per frame with no catch-up burst; low FPS can reduce RPM.

## Unreal: first run

1. Check out this feature branch (or merge the reviewed PR). Close Unreal and
   regenerate project files for AfterfallMobile.uproject. Build the
   AfterfallMobileEditor target, Development Editor / Win64, with UE 5.8.
   This environment has no Unreal build/editor install: UHT, compilation and PIE
   remain explicit validation gates, not claimed passes.
2. Open the existing test map using AFGameModeBase/AAFCharacter or its existing
   Blueprint subclass. Native defaults equip HOUND automatically. Confirm the
   character Blueprint's DefaultWeaponClass is AFHoundWeapon or BP_AF01_Hound.
3. Press Play: LMB/right trigger fires while held; RMB/left trigger aims; R/gamepad
   left face button reloads. A primitive rifle is visible without imported art.
   The stock Engine Cube asset is used for the placeholder, not a borrowed weapon.
4. Put a Leaper and a wall into the existing test map. Aim with the screen center.
   Inspect ammo/heat through the weapon getters or a temporary Blueprint Print
   String bound to OnStateChanged. No finished HUD asset is generated here.
5. For hand attachment, add `Weapon_R` on the player's right-hand skeleton bone.
   Set WeaponAttachSocket and WeaponGripOffset in the character Blueprint. The
   fallback attaches at capsule-relative (25,18,40) cm until that socket exists.
   Tune the offset for your actual player mesh and pose; no player hand/IK art
   was available here. Aiming changes FOV and yaw control, not the movement code.

## Unreal: replacing placeholder art

Create BP_AF01_Hound from AFHoundWeapon. Turn off ShowPrimitiveBlockout. Assign a
combined static preview mesh to WeaponMesh, with origin at Grip_R, scale 1. For
separate moving parts, keep Receiver as WeaponMesh and add the remaining static
components under WeaponRoot using the part offsets below. Leave weapon component
collision disabled so it cannot intercept its own hitscan.

Create `Muzzle` in WeaponMesh's Socket Manager at weapon-root-local (79,0,14) cm
when using the combined mesh. For Receiver alone the root is also Grip_R. Without
the socket, MuzzleFallback is at (78,0,14) cm; move it to the muzzle tip as needed.
The point-light flash and heat light are prototype feedback. For mobile production
replace them with an emissive strip and a cheap muzzle particle/sprite.

- Set MuzzleEffect (Cascade particle) and FireSound/ReloadSound assets if available.
  For Niagara, spawn the system from OnWeaponFired; this avoids requiring a new
  Niagara module dependency in the core weapon.
- OnWeaponFired receives muzzle transform and hit result: drive bolt recoil,
  fire montage, impact VFX and tracers there. Do not subtract ammo or apply damage
  again in Blueprint. The callback represents a successful shot only.
- OnReloadStarted: play the reload montage and move the Magazine component.
  OnReloadFinished(false): return it to rest. OnReloadFinished(true): stop/reset
  the animation. The timer owns ammo transfer; notifies are cosmetic in this pass.
- OnHeatChanged: set a Dynamic Material Instance scalar `Heat` (0–1) and/or
  `HeatColor` on the heat strip. Its blockout material is static orange; animate
  its emission/color in Unreal. Overheated is supplied to the event.
- OnEquippedWeaponChanged: unbind the previous weapon's HUD delegates, bind the
  new weapon's OnStateChanged, then immediately query magazine/reserve/heat and
  reload/overheat getters. Use these to drive Text and Progress Bar widgets.
- Mobile UI: Fire Pressed → StartPrimaryFire; Released/cancelled → StopPrimaryFire;
  Aim Pressed/Released → StartAiming/StopAiming; Reload → ReloadWeapon. Do not bind
  both FirePrimary and StartPrimaryFire to the same press.

## Pickup, inventory and future attachments

EquipWeapon accepts an existing unowned AAFWeaponBase within PickupDistance
(250 cm by default), checks bCanBePickedUp, and drops the old weapon. DropWeapon
detaches the actor and clears ownership without resetting ammo or heat. Heat
continues cooling in the world. Death drops the equipped rifle. An actor claimed
by another pawn cannot be equipped. A future interaction/overlap UI calls this
API with its target reference; no automatic pickup radius, interact key or raid
persistence system is added. Dropped actors currently remain at their drop
transform, without physics. Inventory item counting is unchanged; weapons are
not silently added to its consumable count map.

Future ammo pickups should remove inventory ammo only after a successful grant;
AddReserveAmmo is the weapon's grant point. The weapon class/WeaponId identifies
future loot data; persist per-instance state when implementing raid saves. New
weapons subclass AFWeaponBase, tune defaults, and supply their own mesh/events.
Attachments can use mesh sockets/components; there is no attachment-stat or
replication system in this milestone. This implementation is standalone/local
gameplay, not server-authoritative multiplayer. Do not ship it as network combat.

## Blender

Open a new scene or your working scene, switch to Object Mode, open
`Tools/Blender/afterfall_af01_hound_blockout.py` in Scripting and Run Script.
It creates only the AF01_HOUND collection, replaces only its own previous output,
and does not alter the Leaper, scene units, lighting, camera, rigs or animation.
Save As AF01_HOUND.blend. The supplied .blend already contains the generated asset.

The original stylized blockout follows the supplied concept's asymmetry, offset
cassette, brace stock, recessed mechanism, low optic and four-port muzzle. It is
not a production replica or engineering design. Ammunition technology is left
fictional/undecided. No real-firearm parts or other game assets are imported.

| Object | Pivot in meters (X,Y,Z) | Role |
|---|---|---|
| AF01_Receiver | 0,0,0 | Main static chassis, grip-root origin |
| AF01_Stock | -0.07,0,0.14 | Brace assembly |
| AF01_Grip | 0,0,0 | Right-hand grip |
| AF01_Magazine | 0.22,-0.055,0.055 | Cassette insertion pivot |
| AF01_Optic | 0.12,0,0.225 | Optic base |
| AF01_Muzzle | 0.70,0,0.14 | Muzzle assembly base |
| AF01_HeatGauge | 0.45,-0.058,0.145 | Gauge strip |
| AF01_Bolt | 0.14,-0.01,0.16 | Animate short cosmetic translation along X |
| AF01_Inserts | 0,0,0 | Protected cables/fasteners |

| Socket marker | Root-local Unreal position in cm |
|---|---|
| Muzzle | 79,0,14 |
| Grip_R | 0,0,0 |
| Grip_L | 48,0,7 |
| Magazine | 22,-5.5,5.5 |
| Eject | 12,5.5,17 |
| Mechanical | 14,-1,16 |

Model +X points forward, +Z up, unit coordinates are meters. Socket empties are
reference markers; recreate sockets in Unreal rather than assuming automatic
import. For a simple initial import, duplicate the asset, join meshes on the copy,
set origin to world zero/Grip_R and export the selection as FBX with unit conversion
enabled. Import as static mesh and verify total length about 119 cm; correct axis
orientation in the FBX export/import preview. Do not apply an extra 100x scale on
both ends. For separate parts, export each mesh with its documented pivot at the
FBX origin, then restore its listed offset (meters ×100) in the weapon Blueprint.
The original separated collection is retained for reload/bolt animation work.

## Validation and first tests

Passed here: native C++ state regression compiled with g++ and warnings as errors;
Blender 5.2.2 blockout generation; 9 meshes / 3,264 triangles / 6 markers; UVs;
nondegenerate faces; stable rerun; unrelated object/frame/units/selection preserved.
The art is an early blockout with procedural materials. Atlas/bake textures,
consolidate material slots, build collision/LODs and profile actual mobile draw
calls before production. Unreal materials must be recreated/baked; Blender rust
nodes do not become an Unreal shader on import.

Run the portable regression from the repo root:
`g++ -std=c++17 -Wall -Wextra -Werror -I Source/AfterfallMobile/Public Tests/weapon_state_test.cpp -o weapon_test`
then run weapon_test. With bpy installed:
`python Tools/Blender/tests/test_hound_blockout.py NEW_OUTPUT.blend`.

First PIE acceptance test (not yet run here):

1. Spawn with 30/120; aim; tap fire. Expect one flash/recoil, 29/120 and heat 8.
2. Hold fire: cadence respects the cap; Leaper hears both hits and misses. Release
   and confirm firing stops. Empty/reloading/overheated attempts create no shot.
3. Hit body then a configured weak-point collider: confirm existing damage,
   discovery/flash/break behavior. No additional weapon-side multiplier is applied.
4. Fire 5 rounds slowly, reload: after 2.2 sec expect 30/115. Full/empty-reserve
   reload does nothing. Cancel by drop/equip/death: no ammo granted.
5. Sustain fire to heat 100; expect lock, cooldown, then unlock at 35. Reload
   during lock must not erase heat. Verify no recoil/ammo use while locked.
6. Aim past a wall with the muzzle obstructed: wall blocks the shot even when
   the camera can see the target. Check muzzle/socket alignment and max range.
7. Drop/re-equip the same actor: ammo/heat persist. Refuse another pawn's weapon
   and out-of-range equips. Unpossess/die while firing: no further shots.
8. Test low FPS and mobile touch release/cancel paths, then profile a device build.

The full milestone is implemented in source but is not declared playable-verified
until the UE build and this PIE checklist pass on the target editor.
