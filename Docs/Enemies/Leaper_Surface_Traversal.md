# Leaper surface traversal — first map foundation

The Leaper now has a first-pass runtime layer for climbing selected buildings without replacing the existing white/yellow/red predator behaviour.

## What is implemented

- Ground AI remains NavMesh driven.
- A Leaper can detect a steep obstacle in its travel direction.
- Only approved geometry is climbable by default.
- On contact it switches from normal AI movement to surface crawl.
- Gravity is suspended while attached.
- The visible skeletal mesh aligns to the contacted surface while the Character capsule stays stable.
- Steep surfaces bias movement upward so the Leaper reliably reaches the top of a building.
- Extra edge probes support the first convex wall -> roof transition.
- Once the Leaper reaches a positive-up roof surface with NavMesh, it can hand movement back to normal AI pursuit.
- Yellow/alert state freezes the Leaper on the surface instead of making it fall.
- Pouncing always exits surface crawl first.

## Marking a building climbable

Preferred production setup:

1. Select the building actor, or the specific Static Mesh Component.
2. Add the tag:

   `LeaperClimbable`

3. Make sure the geometry uses WorldStatic or WorldDynamic collision and can be hit by object queries.

You can tag an entire simple warehouse actor, or tag only selected wall/roof components on a more complex building.

## Fast prototype switch

For the first traversal test only, enable:

`Prototype Climb All World Static`

on `BP_LeaperEnemy`.

This lets the Leaper try any steep WorldStatic surface without manually tagging the test building. Turn it back off before building the real map so small props and unwanted scenery do not become traversal surfaces.

## Important Blueprint settings

Under **Afterfall | Leaper | Traversal**:

- Enable Surface Traversal = true
- Allow Scanning Surface Traversal = true for roaming tests
- Climbable Actor Tag = LeaperClimbable
- Max Climb Entry Normal Z = 0.55
- Climb Entry Probe Distance = 180
- Surface Crawl Speed = 235
- Walkable Exit Normal Z = 0.72
- Exit To Nav On Walkable Surface = true

The defaults are already set in C++.

## Roof NavMesh

If `Exit To Nav On Walkable Surface` is enabled, add a Nav Mesh Bounds Volume that also covers the roof.

That gives the first-map sequence:

```text
ground NavMesh
    ->
detect tagged wall
    ->
surface crawl up wall
    ->
probe around roof lip
    ->
align onto roof
    ->
find roof NavMesh
    ->
resume normal predator pursuit
```

If a roof is not navigable, the Leaper stays in surface-crawl mode instead of immediately handing control back to normal AI.

## First test building

Use one simple rectangular warehouse before using a detailed production asset.

Recommended dimensions:

- wall height: 500-800 cm
- roof width: 1000-2000 cm
- clean vertical exterior walls
- flat roof
- no decorative overhang for the first test

Place the player on the far side or roof and put the Leaper approximately 800-1400 cm from the near wall.

Expected result:

1. Leaper pursues normally.
2. Wall blocks the ground route.
3. Entry trace finds the climbable wall.
4. Leaper turns its body visually onto the wall and crawls upward.
5. At the roof lip it acquires the roof surface.
6. If roof NavMesh exists, normal pursuit resumes on top.

## Current limitations

This is the safe first-pass system, not the final arbitrary 3D navigation solution.

It does not yet provide:

- concave inside-corner traversal
- reliable ceiling crawling
- automatic route scoring between several buildings
- rooftop jump-link selection
- procedural generation of traversal points
- IK placement for each individual foot on irregular geometry

Those should come after the wall -> roof sequence is stable on the actual Leaper rig.

## Next pass

After the warehouse test is visually correct, extend traversal with:

1. roof-edge descent
2. wall-to-wall corner crawling
3. explicit rooftop jump points
4. ambush/perch points
5. route scoring so the Leaper chooses climb routes that intercept the player
6. leg IK traces so every foot grips the contacted surface
