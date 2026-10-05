# Leaper V26 fitted combat armor

Fitted and tested against the newly uploaded Leaper_Standard_Final(1).blend.
This replaces the V25 preview's straight sleeves with tapered segmented shells,
compact servo drums, supported actuators/cables, exposed structural spars and a
low faceted thorax. The alien face geometry, mandible/head movement, 33 existing
bones, actions and NLA remain intact. Decorative materials use dark metallic
steel with sparse rust and restrained orange marks. Existing material datablocks
are retained; decorative object slots are reassigned. Gameplay slots and shaders
are left alone.

## Use

Open your current scene, Save As a copy, switch to Object Mode, then open
`Tools/Blender/afterfall_leaper_v26_fitted_combat_armor.py` in the Text Editor
and click Run Script. Alternatively open the supplied V26 .blend, which already
has this pass applied. Do not run the V24/V25 passes over V26 afterward.

Superseded torso, leg armor, decorative ball joints, V25 details and V24 leg
details are hidden, not deleted. Original geometry and skin weights are intact.
V26 retains their previous hide flags in custom properties. Reopen the source
copy for a full rollback including decorative material slots. Rerunning V26
replaces only V26-generated objects and does not accumulate duplicate parts.
No save or export is performed by the artist-facing script.

## Validation completed

- Blender 5.2.2 LTS: 473 original mesh geometries/skin weights unchanged.
- 33 bones with the same rest transforms/parents; existing actions/NLA unchanged.
- New rigid attachment verified at frames 1, 18, 36, 54 and 72, error under 1e-6.
- Gameplay material-slot mapping unchanged; rerun geometry/datablock counts stable.
- 193 new component meshes; superseded meshes excluded from the FBX test.
- Front, rear and alert renders inspected.
- FBX export/reimport retained the 33-bone hierarchy, all 10 gameplay material
  aliases and the active animation; all V26 meshes remained skinned.

The input contains alert, face-motion and predator-reaction actions, but no crawl
action. Crawl preservation/playback could not be tested from this file. These
checks establish deformation/export behavior, not exhaustive collision clearance.

## Test in Blender

1. Play the alert action through frames 1–72, face motion through 1–97 and
   predator reaction through 1–78. Inspect knee/hip clearances and head/mandibles.
2. Orbit the model; inspect cable ends, actuator mounts and lower-leg transitions.
3. Check the five weak-point regions and existing armor-cover bone movement.
4. Inspect Material Preview: dark steel should retain highlights and sparse rust.
5. In the scene containing your crawl action, check that full loop too.

## Test in Unreal

1. Export only the existing rig and visible skinned meshes. Disable leaf bones;
   export the intended action. Exclude the hidden superseded armor.
2. Import to a separate test folder using the existing skeleton. Verify bone
   mapping, active clip playback, head tracking and weak-point targeting.
3. Reuse state/weak-point materials: white scanning, yellow alert, red attacking;
   grey dormant weak points, pale yellow/white exposed or hit.
4. Build/bake the new decorative material equivalents: Blender procedural rust
   does not transfer as an Unreal shader through FBX.
5. New shell meshes do not yet implement break-off/loot behavior. Integrate these
   with the game's damage system before replacing production armor. Profile mesh
   sections/draw calls and consolidate for mobile; this is not a mobile LOD pass.

Unreal editor validation remains to be performed on the user's PC. The design
uses the reference's armor language while retaining the existing Leaper proportions.
