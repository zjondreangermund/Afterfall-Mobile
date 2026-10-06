# HOUND connected geometry V03

Run `Tools/Blender/afterfall_af01_hound_v03_connected.py` in Blender's Text
Editor, in Object Mode. The standalone script includes the V02 materials.
Save As a new file first if you have edited your HOUND geometry: this replaces
the generator-tagged HOUND meshes, not just their materials. Untagged scene
objects, including Leaper assets, are left alone. Existing custom HOUND mesh
edits are not migrated; the generated HOUND is rebuilt at its standard origin.

Corrections from the user's front/underside and opposite-side screenshots:

- Extend stock beam into a receiver collar, with side mounting plates.
- Add grip mounting block and magazine well bridging the offset cassette.
- Support the upper rail and optic with continuous mounting surfaces.
- Bridge the forward chassis into the rectangular muzzle assembly.
- Add layered side armor on both sides, supported fasteners, recessed capped
  mechanical housings, cable terminals and magazine protective strips.

The nine logical mesh groups and six socket markers retain their existing
names and documented pivots. Geometry is 5,376 triangles. This is an improved
game-art blockout, not a claim of matching the concept's finished detail and
texture quality. Procedural materials still need baking for Unreal/mobile.

Validation: Blender 5.2.2 generation, UV/face checks, stable rerun, unchanged
unrelated scene object, and hero/opposite underside render inspection. No
weapon gameplay or Leaper code is modified by this pass.
