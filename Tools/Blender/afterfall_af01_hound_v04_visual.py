"""AF-01 HOUND: original Afterfall game-art blockout, Blender 5.2+.

Open Text Editor > Run Script in Object Mode. Creates only AF01_HOUND objects.
Does not save, export, change the camera, rig, animation, lighting or scene units.
Coordinates are meters; +X muzzle, +Z up, grip origin at (0,0,0).
Not engineering geometry or a buildable firearm design.
"""
import bpy
import math
from mathutils import Vector, Matrix

TAG='AfterfallHoundBlockout'
GROUPS=('Receiver','Stock','Grip','Magazine','Optic','Muzzle','HeatGauge','Bolt','Inserts')
PIVOTS={'Receiver':(0,0,0),'Stock':(-.07,0,.14),'Grip':(0,0,0),
        'Magazine':(.22,-.055,.055),'Optic':(.12,0,.225),'Muzzle':(.70,0,.14),
        'HeatGauge':(.45,-.058,.145),'Bolt':(.14,-.01,.16),'Inserts':(0,0,0)}
SOCKETS={'Muzzle':(.79,0,.14),'Grip_R':(0,0,0),'Grip_L':(.48,0,.07),
         'Magazine':(.22,-.055,.055),'Eject':(.12,.055,.17),'Mechanical':(.14,-.01,.16)}


def material(name,color,metal=.8,rough=.4,emission=0):
    m=bpy.data.materials.get('AF01_'+name)
    if m: return m
    m=bpy.data.materials.new('AF01_'+name);m.use_nodes=True
    m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    if name=='Armor':
        n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=24
        ramp=m.node_tree.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position=.68;ramp.color_ramp.elements[0].color=(*color,1)
        ramp.color_ramp.elements[1].position=.83;ramp.color_ramp.elements[1].color=(.16,.048,.012,1)
        m.node_tree.links.new(n.outputs['Fac'],ramp.inputs['Fac'])
        m.node_tree.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
    return m


def build_hound():
    if bpy.context.mode!='OBJECT': raise RuntimeError('Switch to Object Mode first.')
    selected=[o.name for o in bpy.context.selected_objects]
    active=bpy.context.view_layer.objects.active
    active_name=active.name if active else None
    old=[o for o in bpy.context.scene.objects if o.get(TAG)]
    col=bpy.data.collections.new('AF01_HOUND_Staging');bpy.context.scene.collection.children.link(col)
    root=bpy.data.objects.new('AF01_HOUND_ROOT_NEW',None);col.objects.link(root);root[TAG]=True
    root['Asset']='AF-01 HOUND / Machine-Breaker Rifle'
    root['AxisConvention']='+X muzzle, +Z up. Model units meters; Unreal units centimeters.'
    root['OriginalDesign']='Afterfall fictional game prop, based on supplied concept; no real mechanism.'
    mats={'Armor':material('Armor',(.055,.062,.067)), 'Edge':material('Edge',(.15,.16,.17),.9,.34),
          'Dark':material('Dark',(.018,.022,.026),.65,.46),'Rubber':material('Rubber',(.012,.012,.014),.05,.72),
          'Orange':material('ServiceOrange',(.40,.105,.015),.5,.46),
          'Glass':material('OpticGlass',(.04,.12,.105),.25,.2),
          'Heat':material('Heat',(.9,.19,.012),.15,.3,2)}
    groups={key:[] for key in GROUPS}
    def adopt(o,group,key):
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o);o[TAG]=True;o.data.materials.append(mats[key]);groups[group].append(o)
        return o
    def box(group,loc,size,key='Armor',bevel=.0025):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        o=adopt(bpy.context.object,group,key);o.dimensions=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        if bevel:
            mod=o.modifiers.new('Edge chamfer','BEVEL');mod.width=bevel;mod.segments=3
            bpy.ops.object.modifier_apply(modifier=mod.name)
        return o
    def beam(group,a,b,r,key='Edge',sides=24):
        a,b=Vector(a),Vector(b)
        bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=r,depth=(b-a).length,location=(a+b)*.5)
        o=adopt(bpy.context.object,group,key);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
        bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        return o
    def plate(group,outline,y,thick,key='Armor'):
        verts=[(x,y+offset,z) for offset in (-thick/2,thick/2) for x,z in outline]
        n=len(outline);faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]
        faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        mesh=bpy.data.meshes.new('Panel');mesh.from_pydata(verts,[],faces);mesh.update()
        o=bpy.data.objects.new('Panel',mesh);col.objects.link(o);adopt(o,group,key)
        bpy.context.view_layer.objects.active=o
        mod=o.modifiers.new('Panel edge finish','BEVEL');mod.width=.0015;mod.segments=3
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return o
    try:
        # Recessed asymmetrical chassis: side armor leaves the fictional bolt visible.
        box('Receiver',(.22,0,.115),(.47,.073,.055),'Dark')
        # Both sides have a protected mechanism recess, with structural web behind it.
        box('Receiver',(.23,.018,.125),(.46,.025,.030),'Dark')
        plate('Receiver',[(-.04,.10),(-.03,.23),(.075,.24),(.105,.19),(.10,.11)],-.038,.018)
        plate('Receiver',[(.30,.10),(.30,.205),(.36,.223),(.41,.19),(.43,.095)],-.039,.018)
        box('Receiver',(.20,0,.22),(.27,.079,.020),'Edge')
        plate('Receiver',[(.02,.085),(.06,.045),(.31,.045),(.35,.105)],-.037,.021)
        # Protected mechanical recess; abstract piston motif, not a functional action.
        beam('Bolt',(.095,0,.17),(.29,0,.17),.020,'Edge',12)
        for x in (.11,.27): beam('Bolt',(x-.007,0,.17),(x+.007,0,.17),.024,'Orange',12)
        beam('Inserts',(.10,-.018,.128),(.30,-.018,.128),.010,'Dark')
        for x in (.115,.17,.225,.28):
            beam('Inserts',(x,-.018,.117),(x,-.018,.138),.016,'Dark',10)
        # Structural brace stock with open central space and soft butt pad.
        box('Stock',(-.205,0,.16),(.37,.055,.052))
        box('Stock',(-.04,0,.15),(.072,.080,.095),'Dark')
        for y in (-.043,.043):
            box('Stock',(-.052,y,.15),(.072,.015,.085),'Edge')
        beam('Stock',(-.38,0,.16),(-.34,0,-.015),.018,'Edge',8)
        beam('Stock',(-.34,0,-.015),(-.065,0,.03),.016,'Dark',8)
        beam('Stock',(-.065,0,.03),(-.065,0,.16),.013,'Edge',8)
        box('Stock',(-.385,0,.06),(.022,.068,.22),'Rubber')
        box('Stock',(-.25,0,.195),(.20,.067,.018),'Rubber')
        box('Stock',(-.356,-.032,.02),(.02,.008,.043),'Orange',.002)
        # Angled grip and nonfunctional open guard.
        grip=box('Grip',(-.008,0,-.025),(.062,.052,.17),'Rubber');grip.rotation_euler.y=.25
        box('Grip',(.005,0,.063),(.078,.067,.055),'Dark')
        for z in (-.07,-.045,-.02,.005):box('Grip',(-.01,-.029,z),(.041,.005,.004),'Dark',.001)
        beam('Grip',(.025,0,.045),(.11,0,.035),.009,'Dark',8)
        beam('Grip',(.11,0,.035),(.09,0,-.025),.009,'Dark',8)
        beam('Grip',(.09,0,-.025),(.018,0,-.04),.009,'Dark',8)
        # Offset fictional cassette. Pivot at its insertion point, removable as a mesh.
        plate('Magazine',[(.16,.063),(.255,.063),(.28,-.21),(.18,-.225)],-.055,.054)
        box('Receiver',(.207,-.035,.060),(.122,.112,.072),'Dark')
        for y in (-.094,.025):
            box('Receiver',(.207,y,.046),(.125,.012,.056))
        box('Magazine',(.228,-.055,-.217),(.115,.068,.023),'Dark')
        plate('Magazine',[(.175,.03),(.188,.03),(.211,-.192),(.198,-.194)],-.084,.003,'Orange')
        plate('Magazine',[(.216,.023),(.239,.023),(.256,-.175),(.234,-.18)],-.084,.004,'Dark')
        # Forebody protects the heat strip while leaving dark mechanical recesses.
        box('Receiver',(.55,0,.14),(.29,.055,.048),'Dark')
        box('Receiver',(.49,0,.215),(.38,.060,.025),'Dark')
        box('Receiver',(.69,0,.14),(.072,.074,.084),'Dark')
        for s in (-1,1):
            plate('Receiver',[(.41,.176),(.44,.224),(.63,.21),(.69,.18),(.68,.163)],s*.038,.018)
            plate('Receiver',[(.40,.112),(.43,.057),(.66,.067),(.71,.115)],s*.041,.017)
            for x in (.445,.50,.555,.61):box('Receiver',(x,s*.052,.08),(.032,.005,.009),'Dark',.001)
        box('HeatGauge',(.52,-.057,.146),(.20,.012,.031),'Dark',.004)
        for i in range(5):box('HeatGauge',(.47+i*.015,-.065,.146),(.008,.002,.009),'Heat',.001)
        box('Inserts',(.49,0,.053),(.17,.04,.022),'Rubber')
        # Quad-port rectangular muzzle, assembled with genuine open recesses.
        for z in (.079,.201):box('Muzzle',(.742,0,z),(.082,.11,.016),'Armor')
        for y in (-.048,.048):box('Muzzle',(.742,y,.14),(.082,.014,.112),'Armor')
        box('Muzzle',(.742,0,.14),(.082,.008,.112),'Edge',.001)
        box('Muzzle',(.742,0,.14),(.082,.10,.008),'Edge',.001)
        box('Muzzle',(.701,0,.14),(.008,.083,.095),'Dark',.001)
        # Integrated low optic: bridge frame and protected tinted lens.
        box('Optic',(.12,0,.232),(.17,.083,.025),'Dark')
        box('Optic',(.12,0,.246),(.15,.077,.018),'Edge')
        for y in (-.033,.033):plate('Optic',[(.045,.24),(.065,.309),(.165,.309),(.192,.24)],y,.012)
        box('Optic',(.119,0,.31),(.12,.076,.015))
        box('Optic',(.168,0,.276),(.004,.051,.043),'Glass',.001)
        box('Optic',(.075,-.041,.274),(.024,.004,.022),'Orange',.001)
        # Sparse integrated rails, panel bolts and an attached cable run.
        for x in (.33,.375,.42,.465,.51,.555,.60,.645):box('Receiver',(x,0,.226),(.026,.050,.010),'Dark',.001)
        for x,z in ((-.012,.211),(.055,.115),(.326,.19),(.421,.09),(.645,.19),(.657,.09)):
            beam('Inserts',(x,-.055,z),(x,-.061,z),.005,'Edge',6)
        pts=[(.29,-.018,.17),(.33,-.027,.148),(.365,-.026,.137),(.41,-.018,.137)]
        for a,b in zip(pts,pts[1:]):beam('Inserts',a,b,.007,'Rubber',8)
        # Connected second-side panels, service plates and protected mechanical inserts.
        for y in (-.050,.050):
            for outline in [ [(-.04,.105),(-.03,.228),(.075,.235),(.100,.190),(.095,.108)],
                             [(.30,.10),(.30,.205),(.36,.223),(.405,.186),(.425,.098)] ]:
                plate('Receiver',outline,y,.010)
            for x,z in ((-.013,.204),(.071,.13),(.327,.184),(.371,.13)):
                beam('Inserts',(x,y,z),(x,y+(.006 if y>0 else -.006),z),.006,'Edge',8)
            # Armor seams are physical layered plate edges, with supported fasteners.
            plate('Receiver',[(.12,.092),(.13,.068),(.275,.068),(.283,.092)],y,.008,'Edge')
            for x in (.14,.26):beam('Inserts',(x,y,.079),(x,y+(.006 if y>0 else -.006),.079),.004,'Dark',8)
            box('Receiver',(.53,y,.188),(.16,.005,.011),'Edge',.001)
        # Two capped housings anchored into the chassis below the main moving bolt.
        for x in (.16,.245):
            beam('Inserts',(x,-.029,.125),(x,-.055,.125),.016,'Dark',12)
            beam('Inserts',(x,-.051,.125),(x,-.059,.125),.011,'Edge',12)
            beam('Inserts',(x,-.058,.125),(x,-.062,.125),.006,'Orange',10)
        for x in (.104,.285):
            box('Receiver',(x,0,.17),(.018,.070,.062),'Dark')
        # Cable terminals physically meet the mechanism and forward chassis.
        for x,z in ((.29,.17),(.41,.137)):
            beam('Inserts',(x,-.01,z),(x,-.031,z),.012,'Edge',10)
        # Magazine protective ribs, inset panels, service fasteners.
        for y in (-.086,-.024):
            for x in (.174,.248):
                plate('Magazine',[(x,.030),(x+.007,.030),(x+.029,-.192),(x+.022,-.192)],y,.006,'Edge')
            for x,z in ((.182,.035),(.248,.035),(.203,-.194),(.265,-.185)):
                beam('Magazine',(x,y,z),(x,y+(-.005 if y<-.05 else .005),z),.004,'Dark',8)
        # Optic side cheek plates, bolts and a mounted orange service badge.
        for y in (-.043,.043):
            plate('Optic',[(.051,.251),(.070,.301),(.11,.301),(.125,.251)],y,.008)
            for x,z in ((.069,.261),(.087,.290)):
                beam('Optic',(x,y,z),(x,y+(-.006 if y<0 else .006),z),.004,'Edge',8)
        # Muzzle guard trim and corner fasteners; preserve four open ports.
        for y in (-.052,.052):
            for z in (.089,.191):
                beam('Muzzle',(.778,y,z),(.787,y,z),.005,'Dark',8)
        for x in (-.345,-.085):
            for y in (-.032,.032):
                beam('Stock',(x,y,.160),(x,y+(-.007 if y<0 else .007),.160),.007,'Edge',10)

        # V04: tapered continuous side skins and curved barrel shroud.
        for y in (-.043,.043):
            plate('Receiver',[(-.03,.108),(-.025,.207),(.08,.219),(.12,.192),(.29,.192),(.33,.204),(.37,.197),(.40,.158),(.39,.105)],y,.006)
            # Narrow recessed service slit retains visual mechanism exposure.
            box('Receiver',(.205,y+(-.004 if y<0 else .004),.159),(.16,.003,.026),'Dark',.003)
            for x in (.135,.265):
                beam('Inserts',(x,y,.16),(x,y+(-.008 if y<0 else .008),.16),.009,'Edge',24)
        beam('Receiver',(.395,0,.145),(.691,0,.145),.032,'Dark',48)
        for x in (.423,.47,.517,.564,.611,.658):
            beam('Receiver',(x-.007,0,.145),(x+.007,0,.145),.036,'Edge',32)
        # Thin sloping cheek plate connects stock and receiver silhouette.
        for y in (-.03,.03):
            plate('Stock',[(-.36,.17),(-.33,.193),(-.115,.193),(-.06,.168),(-.07,.145),(-.35,.145)],y,.008)
        # Fine seams and restrained service markings.
        for y in (-.05,.05):
            plate('Receiver',[(.315,.173),(.326,.198),(.357,.198),(.369,.173)],y,.002,'Orange')

        # Consolidate into nine logical meshes with documented animation pivots.
        for key,parts in groups.items():
            part_meshes=[o.data for o in parts]
            bpy.ops.object.select_all(action='DESELECT')
            for o in parts:o.select_set(True)
            bpy.context.view_layer.objects.active=parts[0]
            bpy.ops.object.join();o=bpy.context.object;o.name='AF01_'+key+'_NEW'
            for data in part_meshes:
                if data.users==0:bpy.data.meshes.remove(data)
            # Freeze transformed geometry to world then rebase it at logical pivot.
            matrix=o.matrix_world.copy();pivot=Vector(PIVOTS[key])
            for v in o.data.vertices:v.co=matrix@v.co-pivot
            o.matrix_world=Matrix.Identity(4);o.location=pivot;o.parent=root
            o['Part']=key;o['PivotMeters']=list(pivot);o[TAG]=True
            bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(island_margin=.02)
            bpy.ops.object.mode_set(mode='OBJECT')
        for name,pos in SOCKETS.items():
            o=bpy.data.objects.new('SOCKET_'+name+'_NEW',None);col.objects.link(o)
            o.parent=root;o.location=pos;o.empty_display_type='ARROWS';o.empty_display_size=.035;o[TAG]=True
            o['UnrealSocketName']=name
        # Only the generator's prior HOUND output is replaced; other scenes untouched.
        for o in old:
            data=o.data;bpy.data.objects.remove(o,do_unlink=True)
            if isinstance(data,bpy.types.Mesh) and data.users==0:bpy.data.meshes.remove(data)
        previous=bpy.data.collections.get('AF01_HOUND')
        if previous:
            for o in list(col.objects):previous.objects.link(o);col.objects.unlink(o)
            bpy.data.collections.remove(col);col=previous
        else:col.name='AF01_HOUND'
        for o in col.objects:
            if o.name.endswith('_NEW'):o.name=o.name[:-4]
        tris=0
        for o in col.objects:
            if o.type=='MESH':o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles)
        root['TriangleCount']=tris
        print('AF01 HOUND complete:',tris,'triangles; 9 logical meshes; 6 socket markers. Save As a new file.')
        return root
    except Exception:
        if bpy.context.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
        for o in list(col.objects):
            data=o.data;bpy.data.objects.remove(o,do_unlink=True)
            if isinstance(data,bpy.types.Mesh) and data.users==0:bpy.data.meshes.remove(data)
        bpy.data.collections.remove(col)
        raise
    finally:
        bpy.ops.object.select_all(action='DESELECT')
        for name in selected:
            o=bpy.data.objects.get(name)
            if o:o.select_set(True)
        o=bpy.data.objects.get(active_name) if active_name else None
        if o:bpy.context.view_layer.objects.active=o




# Embedded material pass: this file runs without companion scripts.
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
        p.inputs['Emission Strength'].default_value = .7
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
    build_hound()
    apply_hound_materials()
