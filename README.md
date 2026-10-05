# Afterfall Mobile

Original third-person mobile extraction shooter prototype built for Unreal Engine 5.8.3.

> **Development codename only:** AFTERFALL. The final commercial title will be changed before release.

## V0.1 goal

Prove the core loop on Android:

**Deploy → Explore → Fight machines → Loot → Extract → Return to base**

The first playable slice is intentionally small:
- Third-person player controller
- Health/damage system
- Enemy base framework
- Scout / Tracker / Leaper / Bastion archetypes
- Leaper pounce prototype
- Loot/extraction architecture
- Mobile-first performance settings
- Samsung Galaxy A15 as the first real-device baseline

## Engine

- Unreal Engine **5.8.3**
- C++
- Android first
- 30 FPS baseline on Galaxy A15, scalable upward for stronger devices

## Important

This project is an original game. Do not copy ARC Raiders characters, assets, maps, names, audio, UI, story, or distinctive visual designs. High-level extraction-shooter mechanics can inspire the loop, but all production assets and worldbuilding must be original.

See:
- `Docs/GAMEPLAY_V0_1.md`
- `Docs/ENEMIES_V0_1.md`
- `Docs/MOBILE_TARGET.md`

## Current Leaper face

The alien predator face pass is `Tools/Blender/afterfall_leaper_v17_alien_predator_face.py`.
Run it in the existing final Blender scene. See [setup and export](Docs/Enemies/Leaper_V17_Alien_Predator.md).

For centering and moving mandibles, run `Tools/Blender/afterfall_leaper_v18_centered_mandible_motion.py`
on the existing V1.7 scene. Press Space over the 3D view to play the facial loop.
See [V1.8 motion and export](Docs/Enemies/Leaper_V18_Centered_Motion.md).

For the wider predator threat flare and runtime sensing/head tracking, run
`Tools/Blender/afterfall_leaper_v19_predator_reaction_motion.py` on the saved
V1.8 `.blend`. See [V1.9 predator reaction](Docs/Enemies/Leaper_V19_Predator_Reaction.md).

## Leaper predator behaviour

The current white → yellow → red predator AI, autonomous crawl, independent head scan,
sound investigation, alert stance and attack flow are documented in
`Docs/Enemies/Leaper_Predator_Behaviour.md`.

Blender alert stance generator:
`Tools/Blender/afterfall_leaper_v21_predator_alert_stance.py`.
