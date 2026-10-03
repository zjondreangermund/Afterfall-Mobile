# Robot Enemy V0.1 Specifications

The current concept sheet is reference for role and mood only. Final production meshes must be original.

## Scout Drone
**Role:** reconnaissance / harassment

- Flies above terrain and checks suspicious sounds.
- Blue search state; warning state changes visually and audibly.
- Pings nearby machines when it confirms a player.
- Low armor.
- Weak point: central sensor/core.
- Destroying it quickly prevents escalation.

## Tracker
**Role:** fast ground hunter

- Runs in pairs or small packs.
- Flanks instead of charging in a straight line.
- Short-range burst attack.
- Weak point: exposed sensor module.
- Damaging a leg reduces movement speed.

## Leaper
**Role:** ambush / pounce

This is the signature V0.1 enemy.

State flow:
**Stalk → Line up → Compress legs → Landing warning → Pounce → Impact → Recovery**

Rules:
- Pounces only inside configured min/max range.
- Player gets a short ground warning before impact.
- Landing causes radial damage/stagger.
- Rear jump actuators are destructible weak points.
- Destroying one actuator reduces pounce range.
- Destroying both removes long pounces and forces ground pursuit.
- Missed pounce creates a short punish window.

The initial C++ class already contains the ballistic pounce and radial landing damage foundation.

## Bastion
**Role:** siege / area denial

- Very slow.
- Heavy frontal armor.
- Strong ranged cannon.
- Controls high-value loot zones.
- Cannon has a visible/audio charge-up.
- Weak point should only be clearly vulnerable from flank/rear.
- Armor panels can be broken to create new damage windows.

## Performance rule

Enemy logic must be distance-tiered:
- **Near:** full perception/combat tick.
- **Medium:** reduced update frequency.
- **Far:** cheap simulation only.
- **Very far:** dormant/despawned where appropriate.

This is mandatory for the Android target.
