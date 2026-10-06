"""Run in the existing HOUND scene: materials only, no mesh/rig changes.
Blender 5.2+. Procedural shaders must be baked to textures for Unreal/mobile.
Uses tagged HOUND objects only; rerunning reuses seven dedicated materials.
"""
import bpy

PREFIX = 'AF01_HOUND_V02_'
PREVIEW_MATERIALS = True
PALETTE = {
    'Armor': ((.075, .085, .095), .92, .29),
    'Edge': ((.30, .33, .36), .95, .24),
    'Dark': ((.025, .032, .04), .85, .34),
    'Rubber': ((.012, .015, .018), .0, .65),
    'ServiceOrange': ((.55, .13, .015), .30, .35),
    'OpticGlass': ((.025, .12, .11), .3, .15),
    'Heat': ((1.0, .19, .008), .1, .27),
}


def make_material(kind):
    color, metal, rough = PALETTE[kind]
    name = PREFIX + kind
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1)
    n, links = mat.node_tree.nodes, mat.node_tree.links
    n.clear()
    def node(t, label, x, y):
        q = n.new(t); q.label = label; q.location = (x, y); return q
    p = node('ShaderNodeBsdfPrincipled', kind, 650, 100)
    out = node('ShaderNodeOutputMaterial', 'Surface', 950, 100)
    links.new(p.outputs['BSDF'], out.inputs['Surface'])
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    if kind == 'Heat':
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = 2.5
        return mat
    if kind == 'OpticGlass':
        p.inputs['Coat Weight'].default_value = .5
        p.inputs['Coat Roughness'].default_value = .1
        return mat
    coord = node('ShaderNodeTexCoord', 'Object coordinates', -1000, 100)
    mapping = node('ShaderNodeVectorMath', 'Fine lengthwise brushing', -800, -200)
    mapping.operation = 'MULTIPLY'
    mapping.inputs[1].default_value = (5, 850, 850)
    links.new(coord.outputs['Object'], mapping.inputs[0])
    grain = node('ShaderNodeTexNoise', 'Brushed machining grain', -600, -200)
    grain.inputs['Scale'].default_value = 1
    grain.inputs['Detail'].default_value = 2
    links.new(mapping.outputs['Vector'], grain.inputs['Vector'])
    r = node('ShaderNodeMapRange', 'Subtle roughness variation', 170, -170)
    r.inputs['To Min'].default_value = max(.12, rough - .07)
    r.inputs['To Max'].default_value = rough + .10
    links.new(grain.outputs['Fac'], r.inputs['Value'])
    links.new(r.outputs['Result'], p.inputs['Roughness'])
    bump = node('ShaderNodeBump', 'Microscopic surface only', 400, -300)
    bump.inputs['Strength'].default_value = .16
    bump.inputs['Distance'].default_value = .00007
    links.new(grain.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], p.inputs['Normal'])
    if kind in ('Armor', 'Dark', 'ServiceOrange'):
        noise = node('ShaderNodeTexNoise', 'Sparse weathering islands', -800, 400)
        noise.inputs['Scale'].default_value = 65
        noise.inputs['Detail'].default_value = 3
        links.new(coord.outputs['Object'], noise.inputs['Vector'])
        mask = node('ShaderNodeValToRGB', 'Keep almost all surface metal', -560, 400)
        mask.color_ramp.elements[0].position = .71
        mask.color_ramp.elements[1].position = .81
        links.new(noise.outputs['Fac'], mask.inputs['Fac'])
        mix = node('ShaderNodeMixRGB', 'Small oxidation flecks', -150, 400)
        mix.inputs[1].default_value = (*color, 1)
        mix.inputs[2].default_value = (.115, .038, .012, 1)
        links.new(mask.outputs['Color'], mix.inputs[0])
        links.new(mix.outputs['Color'], p.inputs['Base Color'])
        metallic = node('ShaderNodeMapRange', 'Oxidation is non-metallic', 170, 350)
        metallic.inputs['To Min'].default_value = metal
        metallic.inputs['To Max'].default_value = .05
        links.new(mask.outputs['Color'], metallic.inputs['Value'])
        links.new(metallic.outputs['Result'], p.inputs['Metallic'])
    return mat


def apply_hound_materials():
    targets = [o for o in bpy.context.scene.objects
               if o.type == 'MESH' and o.get('AfterfallHoundBlockout')]
    if not targets:
        raise RuntimeError('Open the AF01 HOUND blockout .blend first; no tagged HOUND meshes found.')
    assignments = []
    for obj in targets:
        for i, slot in enumerate(obj.material_slots):
            if not slot.material:
                continue
            name = slot.material.name
            kind = name[len(PREFIX):] if name.startswith(PREFIX) else name.removeprefix('AF01_')
            if kind in PALETTE:
                assignments.append((obj, i, kind))
    if not assignments:
        raise RuntimeError('No recognized HOUND material slots found. No changes made.')
    mats = {kind: make_material(kind) for kind in sorted({a[2] for a in assignments})}
    for obj, index, kind in assignments:
        # Object-linked slots prevent changing another mesh sharing this material/data.
        obj.material_slots[index].link = 'OBJECT'
        obj.material_slots[index].material = mats[kind]
    if PREVIEW_MATERIALS:
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces.active.shading.type = 'MATERIAL'
                    area.spaces.active.shading.use_scene_world = False
                    area.spaces.active.shading.use_scene_lights = False
    print('HOUND V02 materials applied:', len(targets), 'meshes. Save As a new file.')
    return targets


if __name__ == '__main__':
    apply_hound_materials()
