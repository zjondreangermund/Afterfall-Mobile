# Traversal visual pass

The native movement code now exposes enough state for the Animation Blueprint to stop looking like a walking mannequin during traversal.

## Runtime values exposed by AAFCharacter

- `bIsInAir`
- `VerticalVelocity`
- `TraversalState`
- `TraversalAlpha`
- `IsTraversalActive()`
- `IsHanging()`

The weapon is automatically hidden while vaulting, mantling or hanging when:
`bHideWeaponDuringTraversal = true`

This is a temporary hands-free visual until a dedicated holster socket/animation is authored.

## Animation Blueprint states to add

### Locomotion
- Ground locomotion
- JumpStart
- FallLoop
- Land

Transitions:
- Ground -> JumpStart when `bIsInAir` becomes true and `VerticalVelocity > 0`
- JumpStart -> FallLoop when `VerticalVelocity <= 0`
- FallLoop -> Land when `bIsInAir` becomes false
- Land -> Ground when landing animation completes

### Traversal overlay/state machine
Use `TraversalState`:
- Vaulting -> low obstacle vault animation
- Mantling -> high mantle/climb-up animation
- Hanging -> ledge hang idle
- Hanging + MoveRight -> ledge shimmy
- Hanging -> Mantling -> climb-up animation

## Production polish order

1. Fix jump/fall/land first so the character never walks in the air.
2. Add low vault animation with one hand contacting the obstacle and legs clearing it.
3. Add mantle animation for chest-high walls.
4. Add ledge hang pose.
5. Add climb-up animation.
6. Add hand IK to the detected ledge top.
7. Add foot IK/planting during vault/mantle.
8. Replace temporary weapon hide with holster-to-back plus draw/put-away animations.
9. Add motion warping for exact obstacle alignment.

## Motion warping target

For final quality, the traversal code should drive animation alignment to:
- wall hit point
- ledge top point
- landing point

Motion Warping can then correct root motion so the hands and feet meet the obstacle precisely instead of the capsule simply following a curve.

## Current mechanics changes

The ledge climb now tests several safe standing depths on top of the ledge instead of a single capsule destination. This reduces the chance of getting stuck when the first mantle target overlaps the platform edge.
