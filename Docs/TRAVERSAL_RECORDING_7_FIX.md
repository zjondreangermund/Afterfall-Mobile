# Recording 7 traversal corrections

This patch builds on main without changing the obstacle course or imported assets.

## Fixed in native code

- Root translation is extracted and discarded on cached, transient animation copies. Scripted capsule movement is the only movement source; original animation assets are not edited.
- Traversal clears the measured obstacle before moving across it. Full-size capsule sweeps validate all three path segments, then sweep again during movement, including phase boundaries on slow frames. A blocked move exits into falling instead of teleporting to its destination.
- Vault landings must be below the obstacle top and within 60 cm of the approach floor. Wide platform tops use the mantle route instead.
- Character facing follows the wall normal. Shimmying rechecks the lip, updates the saved climb destination, and stops at missing ledges or sharp corners.
- Climb-up checks for actual supporting ground. It uses the stand mantle instead of replaying a 2.5 m ground approach from a hanging pose.
- The hang pose freezes at the requested animation time, independent of timer overshoot. A failed climb request retains its hang timer. Dropping or an interrupted traversal restores previous gravity/rotation settings and briefly prevents immediate re-grabbing.
- Walking off an edge starts the falling animation. Spring-arm collision stays enabled; the local body is hidden from its owner when the camera is pushed inside it.

## Verification

The standalone C++ regression test covers the production path timing, phase continuity, endpoints, monotonic movement and capsule clearance for 60/100/145/170/260 cm obstacles with two capsule heights:

```sh
g++ -std=c++17 -Wall -Wextra -Werror -I Source/AfterfallMobile/Public Tests/traversal_path_test.cpp -o /tmp/afterfall_traversal_test
/tmp/afterfall_traversal_test
```

Unreal Engine 5.8 and the imported Content assets are not present in the validation environment. The complete game has not been compiled or play-tested here. The clearance path is conservative: a standing capsule will reject openings too short for it even if an animation could visually tuck through.

## Check in Unreal

1. Close Unreal, update the source, and rebuild the AfterfallMobileEditor target before reopening the project (the reflected character class changed).
2. Repeat Recording 7 on low walls, wide platforms, tall ledges and from an angled approach. The body should no longer travel independently of its capsule or teleport through the obstacle.
3. Hang, shimmy sideways, then climb; confirm the landing stays at the new sideways position. Try moving past the platform end and climbing beneath a low ceiling.
4. Drop while holding forward: confirm there is no immediate re-grab. Walk off a platform and confirm the fall animation plays.
5. Rotate the camera against a wall: the body should hide only for the owning camera, then return when there is space.
6. Repeat at low frame rate and with a blocking prop inserted during traversal.

Exact hand/foot contact still depends on the retargeted clips. This patch does not author hand IK or motion-warping contact windows, and cannot establish their timing without the project's animation assets. Check the hand contact and `HangPoseFreezeFraction` in the actual project before treating the visuals as final.
