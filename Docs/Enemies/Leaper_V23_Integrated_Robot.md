# Leaper v23: integrated industrial robot details

Run `Tools/Blender/afterfall_leaper_v23_integrated_robot_details.py` on the existing
`Leaper_Standard_Final.blend`. This is an additive detail pass, not a model or rig
rebuild. It continues main at `8c64e6e` (industrial machine palette).

## Why this replaces v22

The three October 5 screenshots show detached ankle/neck rings, high floating
heat-sink blocks, and lights outside their intended housings. The supplied
`afterfall_leaper_v22_robot_detail_pass.py` reads mesh object origins as physical
anchors, builds against the active frame, uses fixed world-axis offsets, and
bone-parents freshly created primitives. Object origins are not necessarily at
mesh centers, and pose-space placement is not a reliable rest-space binding.

v23 instead authors mesh vertices in armature REST coordinates and weights each
part to an existing deform bone. Bone-local axes supply orientations and each
limb's dimensions supply its scale. Body service plates use an inscribed footprint
on an actual evaluated rest-mesh triangle, not its object origin or bounding box.
Unknown/mixed body attachments are skipped with a console note rather than guessed.

## Changes

- Removes only v22/v23 tagged mesh/curve details belonging to the selected final
  Leaper root/rig. Untagged artist objects and other rigs are not removed.
- Replaces open torus rings with small solid servo housings and six-sided bolts.
- Adds inner structural rails; sleeve, rod and seal assemblies; metal end brackets;
  paired protected cable runs and clamps. Every part has an existing bone binding.
- Adds a compact neck spindle/socket and short harness runs.
- Adds up to two small surface-mounted service panels, dark seams, vents and bolts.
- Uses titanium, steel, gunmetal, steel piston rods, rubber cables and sparse orange
  bands. Known shell materials receive object-local overrides; other objects sharing
  their old materials or mesh datablocks keep their previous appearance.
- Removes v22's permanently yellow knee lights and permanently glowing rear weak-point
  lookalikes. Existing face/status/weak-point geometry and materials are retained.

No bones, constraints, handlers, drivers, action curves or NLA tracks are added or
edited. No existing mesh vertices, shape keys, skin weights or modifiers are edited.
Current pose/rest display is restored; the current action, frame, range, selection,
FPS, cameras and lights are retained. The script does not save or export a file.

All new details are meshes with Armature modifiers. There are no Curve objects to
convert for FBX. New geometry is staged before old tagged details are replaced.
Running the pass again replaces its own details and frees their unused mesh data.
Tweaks to the six `AF_V23_*` materials are retained on rerun.

## Run in Blender

1. Open your existing `Leaper_Standard_Final.blend` and use **File > Save As** to
   create `Leaper_Standard_V23_Test.blend` first.
2. Switch to **Object Mode**. In **Scripting**, choose **Open**, select the v23 `.py`,
   then click **Run Script**. No earlier detail pass needs to be rerun.
3. In the Outliner, inspect `LEAPER_V23_IntegratedDetails`. Check the printed result
   in Blender's system console for skipped service panels or other notes.
4. View in **Material Preview** with viewport overlays off to distinguish metal
   geometry from the large visible armature bones.
5. Check front, rear, both sides and underneath: no old v22 floor rings or raised fins;
   joint housings centered on hinges; cable ends inside glands/clamps; panels touching
   the shell. Check for new details buried inside armor or intersecting claws.
6. Play the existing crawl from beginning to end, then the alert action. Scrub the
   widest leg extension, tightest bend and transition poses. Watch ankles/knees for
   separation and armor intersections. Do not rerun an animation generator merely to
   select/play an already existing action.
7. Play existing head/mandible movement. Check the neck at maximum yaw/pitch and verify
   the face remains centered. Confirm the original weak-point bones and cover bones
   are still present.
8. Run v23 a second time while stopped at a different frame. There should be no extra
   duplicate detail objects, no changed action, and no timeline reset.
9. Save the test copy once satisfied. Keep the original until the UE test succeeds.

A failed preflight leaves the scene unchanged. An error while generating staged
geometry removes those staged details and preserves old details. If an unexpected
error occurs during final replacement, reopen the saved test copy before retrying.

## Unreal import and exact checks

Use a duplicate/test Skeletal Mesh asset for the first import, sharing the current
Leaper Skeleton. Keep your existing tested export scale/axis settings.

1. Export the current armature and all required visible original meshes **plus**
   `LEAPER_V23_IntegratedDetails`; preserve the existing material helper meshes/slots
   described in the v17/v18 setup. Exclude floor, reference figures, cameras and lights.
2. Export as FBX with Mesh and Armature, **Add Leaf Bones off**. Do not rename bones,
   create a new skeleton, apply the Armature modifiers, or change the rest pose.
   For a geometry-only update, disable animation export; existing animations remain
   on the existing skeleton. Preserve the established deform-bone export setting.
3. Import to a new test asset using the existing Skeleton. Reject/report any skeleton
   hierarchy mismatch rather than approving a skeleton rewrite.
4. Verify the new details are part of the Skeletal Mesh, not separate static props.
   Preview both existing crawl and alert Animation Sequences and rotate the head via
   the existing AnimBP setup. Verify claws, face, sockets and collision alignment.
5. Retain these exact gameplay slot/material names. Do not allow reimport to silently
   substitute the new decorative `AF_V23_*` materials for these slots:

| Existing slot/material | Expected behavior |
| --- | --- |
| `LEAP_SIGNAL_Scan_White` | White while scanning |
| `LEAP_SIGNAL_Alert_Yellow` | Yellow after detection/noise |
| `LEAP_SIGNAL_Attack_Red` | Red during attack |
| `LEAP_WP_Eye_Grey` and the existing limb weak-point grey slots | Grey before exposure |
| `LEAP_WP_Discovered_PaleYellow` | Pale yellow/white after exposure |
| `LEAP_WP_Hit_WhiteYellow` | Pale yellow/white damage flash |

6. In PIE, test idle scanning, a noise stimulus, visual detection, attack and losing the
   target. Check existing head tracking still works. Shoot each configured weak point;
   check hitbox alignment, grey-to-pale feedback, cover removal and existing loot logic.
   The internal details should remain when an existing cover bone is hidden/scaled away.
7. FBX does not reproduce all Blender material shading automatically. Check the six
   new materials in Unreal and set Base Color, Metallic and Roughness from the table
   below as needed. Their emissive input should stay black. Brushed anisotropy is a
   Blender preview finish; author an equivalent UE material if desired.
8. Only after these checks, replace/reimport the production mesh. Verify material slot
   names again because the asset now includes six new decorative materials.

| New decorative material | Linear base RGB | Metallic | Roughness |
| --- | --- | ---: | ---: |
| `AF_V23_Titanium` | 0.145, 0.165, 0.185 | 0.92 | 0.38 |
| `AF_V23_Steel` | 0.285, 0.315, 0.345 | 0.96 | 0.30 |
| `AF_V23_Frame` | 0.075, 0.088, 0.102 | 0.94 | 0.42 |
| `AF_V23_Chrome` | 0.36, 0.39, 0.42 | 0.98 | 0.22 |
| `AF_V23_Cable` | 0.022, 0.026, 0.031 | 0.05 | 0.64 |
| `AF_V23_Orange` | 0.52, 0.12, 0.018 | 0.65 | 0.36 |

## Validation and limits

Automated tests run with real **Blender bpy 5.2.0 LTS**, using a synthetic final rig
with transformed/nonuniformly scaled parents, animated head/legs, weak-point bones,
material slots, multiple actions and an existing NLA track:

- Four tests pass: original rig/animation and shared-material preservation;
  rest-space skin attachment across four animation frames; reruns at different frames
  with stable geometry/data counts; preflight/staging failure behavior; animated FBX
  export/import retaining the bone set and deforming mesh details.
- Four-legged fixture: **222 detail objects, 7,256 triangles, six new materials**.
  This is an authoring pass, not a mobile LOD optimization pass.
- A fixture render was inspected for compact connected segment construction. It is
  not a render of the user's final Leaper.

The actual `Leaper_Standard_Final.blend` was not supplied during this implementation.
Its exact armor clearances, hidden geometry, and maximum animation poses therefore
remain unverified. Blender 5.2.2 and an Unreal Engine 5.8 editor were not run here.
The artist's file and a real UE test remain the final acceptance gate.

The actuator sleeves/rods are rigid assemblies on each existing leg segment; their
travel is **not** simulated across joints. Cables stay on their own rigid segments.
This avoids adding bones or Blender-only constraints that would change the game
skeleton. True joint-spanning telescoping mechanisms need a separate rig/AnimBP pass.
No armor-fracture system is added: existing cover bones and break-off gameplay are
preserved, and new structural details bind to head/leg bones rather than cover bones.

Run tests with Blender background mode or Python plus a matching bpy wheel:

```sh
blender --background --factory-startup --python Tools/Blender/tests/test_leaper_v23_details.py
```
