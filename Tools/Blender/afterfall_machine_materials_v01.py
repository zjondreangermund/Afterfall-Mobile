"""Afterfall shared industrial machine material pass V1.0.

Run this on an existing Afterfall Blender machine scene.
It does NOT rebuild geometry, rigs, actions, weak points, or animations.
It upgrades known machine materials from near-black / bone-white placeholders
to a coherent robot-metal language:

- dark titanium armor
- brighter brushed-steel edges and armor caps
- dark gunmetal inner mechanisms
- bright steel hydraulics / barrels
- orange industrial accents
- grey dormant weak points
- white / yellow / red state lights

Safe to re-run. Save As after checking the result, then re-export the visible
machine meshes to Unreal.
"""

import bpy

VERSION = "1.0"

# Values are intentionally not chrome. The machines should still read clearly
# in dark industrial spaces and keep enough roughness for scratches/dirt later.
PALETTE = {
    "dark_titanium": {
        "base": (0.145, 0.165, 0.185),
        "metallic": 0.92,
        "roughness": 0.38,
    },
    "brushed_steel": {
        "base": (0.285, 0.315, 0.345),
        "metallic": 0.96,
        "roughness": 0.29,
    },
    "gunmetal": {
        "base": (0.075, 0.088, 0.102),
        "metallic": 0.94,
        "roughness": 0.42,
    },
    "hydraulic_steel": {
        "base": (0.36, 0.39, 0.42),
        "metallic": 0.98,
        "roughness": 0.20,
    },
    "industrial_orange": {
        "base": (0.52, 0.12, 0.018),
        "metallic": 0.70,
        "roughness": 0.31,
    },
    "weakpoint_grey": {
        "base": (0.26, 0.285, 0.31),
        "metallic": 0.88,
        "roughness": 0.30,
    },
    "cable": {
        "base": (0.025, 0.028, 0.032),
        "metallic": 0.22,
        "roughness": 0.62,
    },
}

SIGNALS = {
    "scan": {
        "base": (0.82, 0.88, 0.95),
        "metallic": 0.08,
        "roughness": 0.16,
        "emission": (1.0, 1.0, 1.0),
        "strength": 6.0,
    },
    "alert": {
        "base": (0.95, 0.55, 0.04),
        "metallic": 0.08,
        "roughness": 0.16,
        "emission": (1.0, 0.42, 0.01),
        "strength": 8.0,
    },
    "attack": {
        "base": (0.80, 0.025, 0.012),
        "metallic": 0.08,
        "roughness": 0.15,
        "emission": (1.0, 0.015, 0.008),
        "strength": 10.0,
    },
    "weak_discovered": {
        "base": (0.78, 0.70, 0.38),
        "metallic": 0.18,
        "roughness": 0.20,
        "emission": (1.0, 0.88, 0.48),
        "strength": 5.0,
    },
    "weak_hit": {
        "base": (0.98, 0.92, 0.58),
        "metallic": 0.12,
        "roughness": 0.14,
        "emission": (1.0, 0.96, 0.64),
        "strength": 12.0,
    },
}

# Existing material names are kept on purpose so current FBX imports and
# gameplay material lookup logic do not break.
ALIASES = {
    # Leaper V1.7 face
    "LEAP_V17_Obsidian": "dark_titanium",
    "LEAP_V17_CarapaceEdge": "brushed_steel",
    "LEAP_V17_InnerMechanism": "gunmetal",
    "LEAP_WP_Eye_Grey": "weakpoint_grey",

    # Earlier shared machine generator materials
    "M_Armor_BoneWhite": "brushed_steel",
    "M_Armor_DarkWhite": "dark_titanium",
    "M_Mechanical_Dark": "gunmetal",
    "M_Hydraulic": "hydraulic_steel",
    "M_Accent_Orange": "industrial_orange",
    "M_Cable": "cable",

    # Signal/weak-point slots
    "LEAP_SIGNAL_Scan_White": "scan",
    "LEAP_SIGNAL_Alert_Yellow": "alert",
    "LEAP_SIGNAL_Attack_Red": "attack",
    "LEAP_WP_Discovered_PaleYellow": "weak_discovered",
    "LEAP_WP_Hit_WhiteYellow": "weak_hit",

    # Older generator sensor stays red/attack-like.
    "M_Sensor_Red": "attack",
}


def _principled(material):
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError(f"{material.name}: Principled BSDF node not found")
    return bsdf


def _set_input(bsdf, name, value):
    socket = bsdf.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def apply_surface(material, spec):
    bsdf = _principled(material)
    base = spec["base"]

    _set_input(bsdf, "Base Color", (*base, 1.0))
    _set_input(bsdf, "Metallic", spec["metallic"])
    _set_input(bsdf, "Roughness", spec["roughness"])

    # Blender 4/5 Principled naming.
    if "Coat Weight" in bsdf.inputs:
        _set_input(bsdf, "Coat Weight", 0.12 if spec["metallic"] > 0.8 else 0.04)
    elif "Clearcoat" in bsdf.inputs:
        _set_input(bsdf, "Clearcoat", 0.12 if spec["metallic"] > 0.8 else 0.04)

    emission = spec.get("emission")
    strength = spec.get("strength", 0.0)
    if emission:
        if "Emission Color" in bsdf.inputs:
            _set_input(bsdf, "Emission Color", (*emission, 1.0))
        elif "Emission" in bsdf.inputs:
            _set_input(bsdf, "Emission", (*emission, 1.0))
        _set_input(bsdf, "Emission Strength", strength)
    else:
        if "Emission Color" in bsdf.inputs:
            _set_input(bsdf, "Emission Color", (0.0, 0.0, 0.0, 1.0))
        elif "Emission" in bsdf.inputs:
            _set_input(bsdf, "Emission", (0.0, 0.0, 0.0, 1.0))
        _set_input(bsdf, "Emission Strength", 0.0)

    material.diffuse_color = (*base, 1.0)
    material["AfterfallMachinePalette"] = VERSION
    material["AfterfallMachineFinish"] = next(
        (name for name, value in {**PALETTE, **SIGNALS}.items() if value is spec),
        "custom",
    )


def ensure_material(name, finish):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    spec = PALETTE.get(finish) or SIGNALS.get(finish)
    if spec is None:
        raise KeyError(f"Unknown Afterfall machine finish: {finish}")
    apply_surface(material, spec)
    return material


def apply_machine_palette():
    changed = []
    missing = []

    for material_name, finish in ALIASES.items():
        material = bpy.data.materials.get(material_name)
        if material is None:
            missing.append(material_name)
            continue

        spec = PALETTE.get(finish) or SIGNALS.get(finish)
        apply_surface(material, spec)
        changed.append((material_name, finish))

    # Record the standard on known Afterfall roots without changing geometry.
    for root_name in ("LEAPER_ROOT", "MACHINE_ROOT", "ROBOT_ROOT"):
        root = bpy.data.objects.get(root_name)
        if root:
            root["MachineMaterialStandard"] = "Industrial Titanium / Steel"
            root["MachineMaterialPaletteVersion"] = VERSION
            root["MachineSignalRule"] = "White scan; yellow alert; red attack."
            root["MachineWeakPointRule"] = "Grey dormant; pale yellow/white when exposed or hit."

    print("AFTERFALL machine material palette V1.0 applied.")
    for material_name, finish in changed:
        print(f"  {material_name} -> {finish}")
    if missing:
        print("Materials not present in this scene (safe to ignore):")
        for name in missing:
            print("  ", name)

    return changed


if __name__ == "__main__":
    apply_machine_palette()
