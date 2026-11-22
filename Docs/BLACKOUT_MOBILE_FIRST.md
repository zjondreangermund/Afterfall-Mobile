# Blackout Extraction: mobile-first development

22 November 2026. This direction supersedes the PC-first shipping sequence in the earlier design document. Both names remain development codenames.

## First playable target

Android first, Galaxy A15 baseline, landscape touch controls, 30 FPS target measured on hardware. iPhone follows once the core mission works, with a separate iOS packaging and device-validation pass. Windows remains useful for development.

Build one five-minute solo PvE mission: enter an industrial relay station, encounter one Leaper, recover loot, choose between powering a valuable room and the extraction lift, then escape. Preserve existing enemy work while developing the biological art direction separately.

Touch layout: left movement stick, right camera drag, fire, aim, reload, context interaction, crouch and traversal. These controls still need an authored HUD, safe-area validation and real-device testing. Avoid tiny inventory targets and simultaneous multi-button requirements.

## Implemented foundation

`UAFPowerCircuitComponent` exposes an event-driven integer power budget to Blueprints. Rejected allocations leave existing loads intact. Updating a named consumer replaces its load; repeating an allocation does not consume power twice. Machinery can subscribe to `OnCircuitChanged`; new or increased loads emit `OnDisturbance` for a future acoustic director. This component does not implement enemy sensing or networking.

`AAFExtractionZone` optionally requires a powered consumer. Loss of power cancels its countdown. Completion checks power again. Player-controlled characters only can initiate extraction; a second overlap cannot replace an active extractor. Existing unconfigured extraction zones retain their power-free behavior. This remains a solo prototype.

## Unreal setup and acceptance

1. Compile the project in the supported Unreal installation and run automation test `Afterfall.Blackout.PowerChoice`.
2. Add the power component to a breaker actor (default capacity 100).
3. Wire a context-interaction Blueprint to allocate `LootRoom` at 60 units or `ExtractionLift` at 60 units. Disconnect the other consumer before rerouting. Display available units and rejected requests in the HUD.
4. Connect loot-door behavior to circuit changes and query `IsConsumerPowered(LootRoom)`; door interaction and assets are not implemented by this component.
5. Assign the breaker actor to the extraction zone's `PowerCircuitActor`. Keep its consumer name `ExtractionLift`.
6. Verify loot and lift cannot both run, switching returns capacity, and losing lift power during the countdown prevents escape. After restoring power, leave and re-enter the volume to restart.
7. Test successful extraction, leaving the volume, repeated component overlaps and power interruption in Editor. Then package Android and measure frame time, temperature and touch responsiveness on Galaxy A15.

## Remaining milestones

- Author compact test map, mobile HUD, interaction wiring and playable mission.
- Add readable machinery audio and connect disturbance to Leaper investigation.
- Add raid results and transactional shelter stash persistence.
- Profile mobile lighting, materials, AI and memory; validate a signed Android package.
- Validate iOS packaging, safe areas and performance on an identified iPhone.
- Evaluate co-op after the solo loop is reliable.

No packaged APK, completed map, multiplayer implementation or measured FPS is delivered by this source change. Unreal Editor is unavailable in the current development environment, so compilation, Unreal automation and device checks remain pending.
