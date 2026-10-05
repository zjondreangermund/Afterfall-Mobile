# Enemy V0.1 Specifications

The current concept material is reference for role and mood only. Final production meshes must be original.

## Shared machine visual standard

All machine enemies now use the same industrial robot material language:
- dark titanium primary armor
- brushed-steel secondary plates/edges
- dark gunmetal inner mechanics
- brighter steel hydraulics/barrels
- restrained industrial-orange accents
- grey dormant weak points
- white scanning, yellow alert and red attack lights where applicable

Avoid flat-black primary armor: it hides the mechanical form in darker levels.
See `Docs/ART_MACHINE_MATERIAL_STANDARD.md`.

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

## Gun Platform — current six-legged Blender robot
**Working role:** mobile ranged suppression / area control

The six-legged robot we have already modelled is no longer the jumping enemy.

Design direction:
- Twin shoulder/autocannon weapon mounts.
- Alternating left/right burst fire.
- Slow-to-medium movement with a wide, planted firing stance.
- Uses cover lanes and suppresses open ground rather than pouncing.
- Can brace before firing a heavier burst.
- Weapon housings, sensor cluster and selected leg joints can be destructible weak points.
- Destroying one gun reduces burst output.
- Damaging front legs reduces turning/aim stability.
- Current Blender body and rig remain useful; the jump animation work is retained as R&D/reference only.
- C++ class: `AAFGunnerEnemy`.

## Leaper — new elongated freaky creature
**Role:** ambush / pounce / panic enemy

The jump logic now belongs to a separate creature with a much more disturbing silhouette.

Visual direction:
- Long, low body — closer to a machine-centipede / stretched predator than a normal robot.
- Long articulated limbs with unusual proportions.
- Smaller armored head and a deep sensor/mouth cavity.
- Rear body compresses like a spring before launching.
- Able to cling to wreckage, crawl through narrow spaces and suddenly cross large gaps.
- Fast, twitchy ground movement between pounces.
- Designed to look wrong/uncomfortable even while standing still.

State flow:
**Hide/Stalk → Track → Telegraph → Compress → Long Pounce → Impact → Recovery**

Rules:
- Pounces only inside configured min/max range.
- Player gets a short but readable landing warning.
- Landing causes radial damage/stagger.
- Missed pounce creates a punish window.
- Damaging rear mobility organs/actuators can reduce pounce range.
- The existing `AAFLeaperEnemy` C++ class remains the gameplay foundation for this new creature.

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
