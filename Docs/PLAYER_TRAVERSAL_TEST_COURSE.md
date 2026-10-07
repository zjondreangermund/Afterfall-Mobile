# Player traversal test course

This pass adds a native contextual parkour layer to `AAFCharacter` and an automatic greybox test course for PIE/editor testing.

## Controls

- `WASD` — move
- `Space` — jump
- `Space` near a small obstacle — vault
- `Space` near a chest-high obstacle — mantle
- Hold `W` while jumping/falling toward a reachable ledge — auto ledge grab
- `Space` while hanging — climb up
- `A / D` while hanging — shimmy left/right
- `S`, `C`, or `Left Ctrl` while hanging — drop
- `RMB` — aim
- `Q` — switch shoulder

## Traversal states

`EAFTraversalState`:
- Normal
- Vaulting
- Mantling
- Ledge Hang

The character exposes `OnTraversalStateChanged` to Blueprint so proper vault, mantle, hang, climb and landing animations can be layered in later without rewriting the movement logic.

## Context logic

### Normal jump

If no traversable obstacle is directly ahead, Space uses the normal Character jump.

### Small obstacles / window sills

A forward obstacle trace finds the wall and a downward trace finds its top.

If the obstacle is below `VaultMaxHeight`, the character looks for a safe landing beyond it and follows a short arced vault path.

This is also the first-pass "jump through a window" behavior: a low sill with clear space behind it is treated as a vault.

### Mantle

If the obstacle is too high to vault but below `MantleMaxHeight`, the character checks capsule clearance on top and climbs onto it.

### Ledge hang

While falling, if the player is holding forward and a reachable ledge is detected, the character:
- stops falling
- snaps to the ledge
- faces the wall
- enters hanging movement mode

Space then climbs to the top.

### Shimmy

A/D attempts movement along the current wall while a short wall-contact trace keeps the character attached.

## Automatic greybox course

In editor/PIE, `AAFCharacter` defaults to automatically spawning one `AAFTraversalTestCourse` if none already exists.

The course contains:
- flat floor / terrain strip
- 60 cm small vault obstacle
- 100 cm wall
- 170 cm mantle wall
- 260 cm tall jump-and-hang platform
- window frame with a low sill
- small crates
- uneven side platforms
- rough ramp / raised terrain section

The course is built from Engine cube meshes, so no external art is required.

To disable it later:

`BP_AFCharacter -> Class Defaults -> Afterfall | Traversal -> Auto Spawn Traversal Test Course In Editor = false`

## Current animation note

The traversal mechanics are native C++ and work without special animation assets.

For production-quality visuals, connect `OnTraversalStateChanged` in the player's Animation Blueprint and add:
- jump/fall
- vault
- mantle
- ledge hang idle
- shimmy
- climb-up
- drop/land

The gameplay logic can stay unchanged while those animations are polished.
