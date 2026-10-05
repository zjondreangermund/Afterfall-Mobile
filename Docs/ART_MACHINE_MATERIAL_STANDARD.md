# Afterfall Machine Material Standard V1.0

All mechanical enemies should read as manufactured industrial robots, not flat-black creatures.

## Core visual language

### Armor
- Dark titanium main shell.
- Brighter brushed-steel armor caps, edges and exposed wear surfaces.
- Semi-matte finish: metallic, but never mirror chrome.
- Large shapes must remain readable in dark interiors and night lighting.

### Inner mechanics
- Dark gunmetal frames, servo housings and joint interiors.
- Brighter steel pistons, hydraulics, barrels and polished contact surfaces.
- Rubber/cable materials stay very dark but should not be confused with the armor shell.

### Industrial accents
- Burnt/orange metal accents can identify high-load mechanical parts, muzzle rings, braces and service markings.
- Orange is an accent only; it should not replace the signal-state system.

## Shared state-light rule

Every Afterfall machine should use the same readable threat language when applicable:

- **White** — scanning / neutral search
- **Yellow** — suspicious / alert / investigating
- **Red** — confirmed attack

The Leaper runtime already uses these states.

## Weak-point rule

- Dormant weak points: medium steel/grey.
- Discovered/exposed: pale yellow-white.
- Fresh hit: brighter white-yellow flash.
- Broken armor can reveal brighter steel frames, pistons, cables and internal mechanisms.

## Leaper

Use:
- dark titanium carapace
- brushed-steel ridges/edges
- dark gunmetal inner jaw and sockets
- grey dormant eye/weak-point cover
- white/yellow/red state-light arcs
- pale yellow-white weak-point exposure/hit feedback

The predator silhouette stays alien/mechanical, but the materials should clearly read as a robot/machine.

## Gun Platform

Use the same family:
- dark titanium primary housings
- brushed steel armor caps and ammo boxes
- gunmetal braces and internal structure
- bright hydraulic steel barrels/pistons
- industrial orange muzzle/service accents
- red attack sensor

## Future machines

Scout, Tracker, Bastion and later enemies should reuse this material family. Their identity should come from silhouette, proportions, wear, paint markings and role-specific accents — not from unrelated material palettes.

## Blender workflow

For an existing saved machine scene, run:

`Tools/Blender/afterfall_machine_materials_v01.py`

This updates known existing materials in place and does not rebuild geometry, rigs or animation.

Safe workflow:

1. Open the final Blender machine scene.
2. Run `afterfall_machine_materials_v01.py`.
3. Inspect in Material Preview / Rendered view.
4. Save As a new version.
5. Re-export visible machine meshes/animations as needed.
6. Reimport/update materials in Unreal.

The script keeps existing material names so current runtime lookups for the Leaper signal and weak-point slots remain valid.

## Unreal target material

When the first production Unreal master material is created, expose at least:

- Base metal tint
- Metallic
- Roughness
- dirt/wear amount
- edge-wear amount
- emissive signal color
- emissive strength
- damage/weak-point glow

Use material instances per machine instead of duplicating the full shader.


## Weathered / rusted production finish

The cleaner titanium/steel palette remains the structural material language, but the current art direction is **weathered industrial machinery**, not clean silver.

For the Leaper and other exposed field machines:

- primary armor should read as oxidized steel / dark brown metal
- rust should appear in irregular patches rather than a flat brown tint
- seams, recesses and lower areas should carry darker grime
- pistons and moving rods can remain somewhat cleaner and more metallic
- cables remain black rubber
- orange service paint should look burnt/faded, not bright toy plastic
- white/yellow/red threat-state lights remain clean and readable
- dormant weak points remain grey; exposed/hit weak points stay pale yellow-white

Run this after the current detail/material pass:

`Tools/Blender/afterfall_machine_materials_v02_rusted.py`

The rust pass uses procedural Blender nodes and keeps existing material names, rigs, animations, weak-point slots and signal-light materials intact.
