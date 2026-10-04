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
