"""Afterfall shared rusted machine finish V2.0.

Run this AFTER the current Leaper detail/material pass on an existing final scene.

Purpose:
- keep all geometry, rigs, animations and material slot names
- turn clean silver/titanium machine armor into worn industrial steel
- add patchy procedural rust and grime using Blender nodes
- keep hydraulics/rods more metallic than armor
- preserve white/yellow/red signal materials and pale weak-point glow

Safe to re-run. Save As a new .blend after checking the result.

Tested for Blender 5.x style Principled BSDF node inputs.
"""

import bpy

VERSION = "2.0"

# Main visual targets. Values are intentionally earthy and rough.
FINISHES = {
    "armor": {
        "metal": (0.20, 0.16, 0.12),
        "rust": (0.34, 0.095, 0.025),
        "rust_dark": (0.13, 0.055, 0.025),
        "metallic_clean": 0.70,
        "metallic_rust": 0.08,
        "rough_clean": 0.58,
        "rough_rust": 0.88,
        "scale": 4.2,
        "detail": 5.0,
        "distortion": 0.30,
        "bump": 0.12,
    },
    "frame": {
        "metal": (0.095, 0.075, 0.060),
        "rust": (0.25, 0.070, 0.018),
        "rust_dark": (0.070, 0.030, 0.015),
        "metallic_clean": 0.62,
        "metallic_rust": 0.05,
        "rough_clean": 0.68,
        "rough_rust": 0.92,
        "scale": 5.5,
        "detail": 4.0,
        "distortion": 0.35,
        "bump": 0.14,
    },
    "steel": {
        "metal": (0.30, 0.27, 0.23),
        "rust": (0.30, 0.085, 0.020),
        "rust_dark": (0.12, 0.050, 0.020),
        "metallic_clean": 0.78,
        "metallic_rust": 0.10,
        "rough_clean": 0.46,
        "rough_rust": 0.82,
        "scale": 4.8,
        "detail": 5.0,
        "distortion": 0.25,
        "bump": 0.10,
    },
    "hydraulic": {
        "metal": (0.34, 0.32, 0.29),
        "rust": (0.22, 0.060, 0.018),
        "rust_dark": (0.10, 0.040, 0.018),
        "metallic_clean": 0.88,
        "metallic_rust": 0.18,
        "rough_clean": 0.34,
        "rough_rust": 0.76,
        "scale": 6.0,
        "detail": 4.0,
        "distortion": 0.18,
        "bump": 0.07,
    },
    "orange": {
        "metal": (0.30, 0.095, 0.020),
        "rust": (0.40, 0.085, 0.012),
        "rust_dark": (0.11, 0.035, 0.012),
        "metallic_clean": 0.50,
        "metallic_rust": 0.04,
        "rough_clean": 0.70,
        "rough_rust": 0.94,
        "scale": 5.0,
        "detail": 4.0,
        "distortion": 0.28,
        "bump": 0.10,
    },
}

# Explicit material aliases found across current and older Leaper passes.
# Signal / weak-point glow slots are deliberately omitted.
ALIASES = {
    # Current shared materials
    "AF_Metal_DarkTitanium": "armor",
    "AF_Metal_BrushedSteel": "steel",
    "AF_Metal_Gunmetal": "frame",
    "AF_Metal_HydraulicSteel": "hydraulic",
    "AF_Metal_ServiceOrange": "orange",
    "AF_Robot_CableRubber": None,

    # Current / local V2.3-V2.4 names seen in final scene
    "LEAP_FINAL_BlackArmor": "armor",
    "LEAP_V16_BlackArmor": "armor",
    "LEAP_V15_BlackArmor": "armor",
    "LEAP_FINAL_JointSteel": "steel",
    "LEAP_V15_Gunmetal": "frame",

    # V1.7 / V1.3
    "LEAP_V17_Obsidian": "armor",
    "LEAP_V17_CarapaceEdge": "steel",
    "LEAP_V17_InnerMechanism": "frame",
    "LEAP_FINAL_GraphiteArmor": "armor",
    "LEAP_FINAL_MechanicalDark": "frame",

    # Earliest generator names
    "M_Armor_BoneWhite": "steel",
    "M_Armor_DarkWhite": "armor",
    "M_Mechanical_Dark": "frame",
    "M_Hydraulic": "hydraulic",
    "M_Accent_Orange": "orange",
}

PROTECTED_TOKENS = (
    "signal",
    "scan",
    "alert",
    "attack",
    "emission",
    "glow",
    "weak",
    "wp_",
    "sensor_red",
    "cable",
    "rubber",
)


def _principled(mat):
    mat.use_nodes = True
    node = mat.node_tree.nodes.get("Principled BSDF")
    if node is None:
        node = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        node.name = "Principled BSDF"
    return node


def _output(mat):
    out = mat.node_tree.nodes.get("Material Output")
    if out is None:
        out = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        out.name = "Material Output"
    return out


def _clear_afterfall_rust_nodes(mat):
    nodes = mat.node_tree.nodes
    for node in list(nodes):
        if node.get("AfterfallRustNode") == VERSION or node.name.startswith("AF_RUST_"):
            nodes.remove(node)


def _tag(node):
    node["AfterfallRustNode"] = VERSION
    return node


def _set_input(node, names, value):
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return socket
    return None


def _link(tree, out_socket, in_socket):
    if out_socket is not None and in_socket is not None:
        tree.links.new(out_socket, in_socket)


def _mix_node(tree, name, color_a, color_b):
    mix = _tag(tree.nodes.new("ShaderNodeMixRGB"))
    mix.name = name
    mix.blend_type = "MIX"
    mix.inputs[1].default_value = (*color_a, 1.0)
    mix.inputs[2].default_value = (*color_b, 1.0)
    return mix


def apply_rusted_finish(mat, finish_name):
    spec = FINISHES[finish_name]
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links

    _clear_afterfall_rust_nodes(mat)

    bsdf = _principled(mat)
    out = _output(mat)

    # Make sure Principled remains connected to Material Output.
    if not any(link.from_node == bsdf and link.to_node == out for link in links):
        for link in list(links):
            if link.to_node == out and link.to_socket == out.inputs.get("Surface"):
                links.remove(link)
        _link(tree, bsdf.outputs.get("BSDF"), out.inputs.get("Surface"))

    tex = _tag(nodes.new("ShaderNodeTexCoord"))
    tex.name = "AF_RUST_TEXCOORD"
    tex.location = (-900, 120)

    noise = _tag(nodes.new("ShaderNodeTexNoise"))
    noise.name = "AF_RUST_NOISE"
    noise.location = (-700, 160)
    _set_input(noise, ("Scale",), spec["scale"])
    _set_input(noise, ("Detail",), spec["detail"])
    _set_input(noise, ("Roughness",), 0.72)
    _set_input(noise, ("Distortion",), spec["distortion"])
    _link(tree, tex.outputs.get("Generated"), noise.inputs.get("Vector"))

    detail_noise = _tag(nodes.new("ShaderNodeTexNoise"))
    detail_noise.name = "AF_RUST_DETAIL"
    detail_noise.location = (-700, -120)
    _set_input(detail_noise, ("Scale",), spec["scale"] * 3.2)
    _set_input(detail_noise, ("Detail",), 3.0)
    _set_input(detail_noise, ("Roughness",), 0.78)
    _link(tree, tex.outputs.get("Generated"), detail_noise.inputs.get("Vector"))

    ramp = _tag(nodes.new("ShaderNodeValToRGB"))
    ramp.name = "AF_RUST_MASK"
    ramp.location = (-470, 170)
    # Cluster rust into irregular patches rather than uniform brown.
    ramp.color_ramp.elements[0].position = 0.38
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    _link(tree, noise.outputs.get("Fac"), ramp.inputs.get("Fac"))

    rust_mix = _mix_node(
        tree, "AF_RUST_COLOR_MIX",
        spec["metal"], spec["rust"]
    )
    rust_mix.location = (-220, 220)
    _link(tree, ramp.outputs.get("Color"), rust_mix.inputs[0])

    grime = _mix_node(
        tree, "AF_RUST_GRIME_MIX",
        spec["rust_dark"], spec["metal"]
    )
    grime.location = (-220, 20)
    _link(tree, detail_noise.outputs.get("Fac"), grime.inputs[0])

    final_mix = _tag(nodes.new("ShaderNodeMixRGB"))
    final_mix.name = "AF_RUST_FINAL_COLOR"
    final_mix.location = (20, 190)
    final_mix.blend_type = "MULTIPLY"
    final_mix.inputs[0].default_value = 0.26
    _link(tree, rust_mix.outputs.get("Color"), final_mix.inputs[1])
    _link(tree, grime.outputs.get("Color"), final_mix.inputs[2])
    _link(tree, final_mix.outputs.get("Color"), bsdf.inputs.get("Base Color"))

    metallic_mix = _tag(nodes.new("ShaderNodeMapRange"))
    metallic_mix.name = "AF_RUST_METALLIC"
    metallic_mix.location = (-10, -40)
    _set_input(metallic_mix, ("From Min",), 0.0)
    _set_input(metallic_mix, ("From Max",), 1.0)
    _set_input(metallic_mix, ("To Min",), spec["metallic_clean"])
    _set_input(metallic_mix, ("To Max",), spec["metallic_rust"])
    _link(tree, ramp.outputs.get("Color"), metallic_mix.inputs.get("Value"))
    _link(tree, metallic_mix.outputs.get("Result"), bsdf.inputs.get("Metallic"))

    rough_mix = _tag(nodes.new("ShaderNodeMapRange"))
    rough_mix.name = "AF_RUST_ROUGHNESS"
    rough_mix.location = (10, -150)
    _set_input(rough_mix, ("From Min",), 0.0)
    _set_input(rough_mix, ("From Max",), 1.0)
    _set_input(rough_mix, ("To Min",), spec["rough_clean"])
    _set_input(rough_mix, ("To Max",), spec["rough_rust"])
    _link(tree, ramp.outputs.get("Color"), rough_mix.inputs.get("Value"))
    _link(tree, rough_mix.outputs.get("Result"), bsdf.inputs.get("Roughness"))

    bump = _tag(nodes.new("ShaderNodeBump"))
    bump.name = "AF_RUST_BUMP"
    bump.location = (10, -300)
    bump.inputs["Strength"].default_value = spec["bump"]
    bump.inputs["Distance"].default_value = 0.08
    _link(tree, detail_noise.outputs.get("Fac"), bump.inputs.get("Height"))
    _link(tree, bump.outputs.get("Normal"), bsdf.inputs.get("Normal"))

    # Reduce clean clearcoat so armor reads old and weathered.
    if bsdf.inputs.get("Coat Weight") is not None:
        bsdf.inputs["Coat Weight"].default_value = 0.02
    elif bsdf.inputs.get("Clearcoat") is not None:
        bsdf.inputs["Clearcoat"].default_value = 0.02

    mat.diffuse_color = (*spec["metal"], 1.0)
    mat["AfterfallRustFinish"] = VERSION
    mat["AfterfallRustType"] = finish_name


def infer_finish(material_name):
    lower = material_name.lower()

    if any(token in lower for token in PROTECTED_TOKENS):
        return None

    if material_name in ALIASES:
        return ALIASES[material_name]

    # Catch newer scene-fitted aliases without requiring exact names.
    if any(token in lower for token in ("hydraulic", "piston", "rod", "chrome")):
        return "hydraulic"
    if any(token in lower for token in ("joint", "steel", "edge", "collar", "rim")):
        return "steel"
    if any(token in lower for token in ("orange", "service", "accent")):
        return "orange"
    if any(token in lower for token in ("frame", "gunmetal", "mechanic", "inner")):
        return "frame"
    if any(token in lower for token in (
        "armor", "armour", "titanium", "blackarmor", "carapace",
        "shell", "plate"
    )):
        return "armor"

    return None


def apply_rust_to_scene():
    changed = []
    skipped = []

    for mat in bpy.data.materials:
        finish = infer_finish(mat.name)
        if finish is None:
            skipped.append(mat.name)
            continue

        apply_rusted_finish(mat, finish)
        changed.append((mat.name, finish))

    for root_name in ("LEAPER_ROOT", "MACHINE_ROOT", "ROBOT_ROOT"):
        root = bpy.data.objects.get(root_name)
        if root:
            root["MachineMaterialStandard"] = "Weathered industrial steel / rust"
            root["MachineRustPaletteVersion"] = VERSION
            root["MachineFinishRule"] = (
                "Patchy oxidized armor; darker grime; cleaner moving rods; "
                "white/yellow/red signals unchanged."
            )

    print("=" * 72)
    print("AFTERFALL RUSTED MACHINE FINISH V2.0 APPLIED")
    print("Changed materials:", len(changed))
    for name, finish in changed:
        print(" ", name, "->", finish)
    print("Signal / glow / weak-point / cable materials were preserved.")
    print("Save As a new .blend before exporting to Unreal.")
    print("=" * 72)

    return changed


if __name__ == "__main__":
    apply_rust_to_scene()
