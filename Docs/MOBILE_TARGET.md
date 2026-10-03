# Mobile Target

## First physical test device

**Samsung Galaxy A15**

The Galaxy A15 is the practical baseline device for the first Android build. It is not the maximum visual target.

## Performance objective

- Baseline: stable **30 FPS** during real combat.
- Frame budget: **33.3 ms**.
- Prioritize consistent frame time over maximum graphics.
- Stronger devices can later expose 45/60 FPS modes.

## Initial rendering rules

For the A15 test build:
- No Lumen requirement.
- No Nanite requirement.
- Mobile-friendly materials.
- Limit translucent effects.
- Aggressive static and skeletal LODs.
- Keep dynamic shadow-casting lights rare.
- Pool projectiles, VFX and debris.
- Distance-tier AI updates.
- Scalable foliage, view distance and shadows.

## Texture targets

- Hero player: mostly 1K–2K.
- Common enemies: mostly 1K.
- Environment props: 512–1K where possible.
- Avoid 4K textures in the first Android build.

## Real performance test scene

Do not benchmark an empty map. The first representative scene should contain:
- Player.
- 2 Trackers.
- 1 Leaper.
- 1 Scout.
- 1 dormant Bastion.
- A small combat POI.
- Representative dust and weapon VFX.

We optimize against this combat scenario, then scale upward for stronger phones.
