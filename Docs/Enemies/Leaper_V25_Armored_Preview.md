# Leaper V25 armored predator preview

Status: preview for review, not a final reference match or Unreal-validated release.
Based on main a70da945dfddf76f4922ffda8c9ff9aceeae701f. Keeps the latest
weathered material work in main and does not depend on merging PR #8.

## Run in Blender

1. Open your current Leaper scene and Save As a separate copy.
2. Switch to Object Mode. In Scripting > Text Editor > Open, choose
   `Tools/Blender/afterfall_leaper_v25_armored_predator_shell.py`.
3. Click Run Script. The script does not save or export automatically.
4. Inspect the `LEAPER_V25_ArmoredPredator` collection. Hide the collection
   to compare before/after. Rerunning replaces only this pass's tagged objects.

Adds 60 angular leg/thorax armor and bearing meshes, rigidly weighted to existing
bones. Retains the alien face and original geometry/material assignments. Reuses
existing metal finishes where available; fallback materials are dark metal.
No new always-red emitter is added. Existing scanning white, alert yellow,
attacking red and dormant/exposed/damaged weak-point materials are unchanged.

## Checks completed

Tested with bpy/Blender 5.2.2 LTS on the V24 fitted scene derived from the uploaded
Leaper_Standard_Final.blend:

- All 473 pre-existing mesh geometries, vertex weights and material assignments unchanged.
- All 33 bones and their rest transforms/parents unchanged.
- Alert, face-motion and predator-reaction actions and NLA unchanged.
- New mesh attachment checked at frames 1, 18, 36, 54, 72; maximum error below 0.000001.
- Rerun stable: same generated geometry and object/mesh/material counts.
- Front, rear and alert renders inspected as geometry previews.

The supplied scene has no crawl action. Its crawl behavior cannot be verified
from this file. The older supplied V24 scene also predates the user's latest
balanced-weathered finish; its preview renders are lighter than the requested
final gunmetal appearance. Run the script on the user's latest saved scene to
reuse that finish. Armor/hinge clearances and coverage need visual approval.
This pass does not implement armor detachment, damage logic or new hydraulics;
the existing details remain underneath it.

## Blender checks still required

Play the full alert and face-motion ranges, and the crawl action in the scene
that contains it. Orbit around hips, knees, ankles, feet and neck: check for
plate intersections, covered weak points and detached details. Check head scan
and mandible extremes. Toggle the new collection to compare silhouette.
Check Material Preview with the latest balanced finish, then Save As.

## Unreal checks still required

Export a test FBX with the existing armature and visible skinned meshes, no leaf
bones, and the intended animation. Import into a separate test folder using the
existing skeleton. Check the unchanged bone hierarchy, all animation clips,
head tracking and weak-point targeting. Reuse the game's material instances;
procedural Blender weathering does not automatically become an Unreal shader.
Test white/yellow/red states and grey/pale-yellow/white weak points. Confirm any
existing break-off behavior: new shell objects are not automatically registered
as breakable armor. Profile the extra mesh sections before mobile deployment.
