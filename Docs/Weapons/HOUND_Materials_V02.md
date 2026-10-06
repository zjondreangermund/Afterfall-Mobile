# HOUND material pass V02

Open the existing HOUND scene. In Scripting > Text Editor > Open, choose
`afterfall_af01_hound_materials_v02.py`, then Run Script. Save As a new blend.
The script switches 3D viewports to Material Preview with studio lighting.
Set `PREVIEW_MATERIALS = False` if you prefer to retain your current shading mode.

Seven dedicated shaders provide dark reflective gunmetal, brushed steel,
blackened recesses, matte grip rubber, orange service paint, a coated optic lens
and restrained orange heat-bar emission. Sparse oxidation leaves most armor
metallic. Fine procedural grain varies roughness and micro-normal detail.

Only tagged HOUND mesh material slots are assigned. Geometry, UVs, rig,
animations, object transforms and socket markers are not changed. Repeated
runs reuse the same seven shader datablocks. Existing unrelated materials are
not edited. V02 shader customization is reset when rerunning this script.

This is a materials pass on the original blockout, not additional mesh detail.
Heat-bar color is a static Blender preview; gameplay animation remains driven
by the weapon's Unreal `OnHeatChanged` event.

Blender procedural shader nodes do not transfer as Unreal materials through
FBX. Bake base color, roughness, metallic and normal textures before production
mobile use, then recreate the emissive mask in Unreal. This pass adds no polygons.

Validated in Blender 5.2.2: application and rerun complete; seven V02 materials;
mesh vertex coordinates and object transforms remain identical. Preview rendered
in Cycles. No Unreal materials or gameplay code changed.
