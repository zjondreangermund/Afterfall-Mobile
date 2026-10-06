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
    def box(group,loc,size,key='Armor',bevel=.003):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        o=adopt(bpy.context.object,group,key);o.dimensions=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        if bevel:
            mod=o.modifiers.new('Edge chamfer','BEVEL');mod.width=bevel;mod.segments=1
            bpy.ops.object.modifier_apply(modifier=mod.name)
        return o
    def beam(group,a,b,r,key='Edge',sides=10):
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
        o=bpy.data.objects.new('Panel',mesh);col.objects.link(o);return adopt(o,group,key)
    try:
        # Recessed asymmetrical chassis: side armor leaves the fictional bolt visible.
        box('Receiver',(.22,0,.115),(.47,.073,.055),'Dark')
        box('Receiver',(.23,.030,.174),(.46,.030,.082))
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
        box('Stock',(-.23,0,.16),(.32,.055,.052))
        beam('Stock',(-.38,0,.16),(-.34,0,-.015),.018,'Edge',8)
        beam('Stock',(-.34,0,-.015),(-.065,0,.03),.016,'Dark',8)
        beam('Stock',(-.065,0,.03),(-.065,0,.16),.013,'Edge',8)
        box('Stock',(-.385,0,.06),(.022,.068,.22),'Rubber')
        box('Stock',(-.25,0,.195),(.20,.067,.018),'Rubber')
        box('Stock',(-.356,-.032,.02),(.02,.008,.043),'Orange',.002)
        # Angled grip and nonfunctional open guard.
        grip=box('Grip',(-.008,0,-.025),(.062,.052,.17),'Rubber');grip.rotation_euler.y=.25
        for z in (-.07,-.045,-.02,.005):box('Grip',(-.01,-.029,z),(.041,.005,.004),'Dark',.001)
        beam('Grip',(.025,0,.045),(.11,0,.035),.009,'Dark',8)
        beam('Grip',(.11,0,.035),(.09,0,-.025),.009,'Dark',8)
        beam('Grip',(.09,0,-.025),(.018,0,-.04),.009,'Dark',8)
        # Offset fictional cassette. Pivot at its insertion point, removable as a mesh.
        plate('Magazine',[(.16,.063),(.255,.063),(.28,-.21),(.18,-.225)],-.055,.054)
        box('Magazine',(.228,-.055,-.217),(.115,.068,.023),'Dark')
        plate('Magazine',[(.175,.03),(.188,.03),(.211,-.192),(.198,-.194)],-.084,.003,'Orange')
        plate('Magazine',[(.216,.023),(.239,.023),(.256,-.175),(.234,-.18)],-.084,.004,'Dark')
        # Forebody protects the heat strip while leaving dark mechanical recesses.
        box('Receiver',(.55,0,.14),(.29,.055,.048),'Dark')
        for s in (-1,1):
            plate('Receiver',[(.41,.176),(.44,.224),(.63,.21),(.69,.18),(.68,.163)],s*.038,.018)
            plate('Receiver',[(.40,.112),(.43,.057),(.66,.067),(.71,.115)],s*.041,.017)
            for x in (.445,.50,.555,.61):box('Receiver',(x,s*.052,.08),(.032,.005,.009),'Dark',.001)
        box('HeatGauge',(.52,-.057,.146),(.20,.012,.031),'Dark',.004)
        for i in range(12):box('HeatGauge',(.435+i*.014,-.065,.146),(.009,.004,.018),'Heat',.001)
        box('Inserts',(.49,0,.053),(.17,.04,.022),'Rubber')
        # Quad-port rectangular muzzle, assembled with genuine open recesses.
        for z in (.079,.201):box('Muzzle',(.742,0,z),(.082,.11,.016),'Armor')
        for y in (-.048,.048):box('Muzzle',(.742,y,.14),(.082,.014,.112),'Armor')
        box('Muzzle',(.742,0,.14),(.082,.008,.112),'Edge',.001)
        box('Muzzle',(.742,0,.14),(.082,.10,.008),'Edge',.001)
        box('Muzzle',(.701,0,.14),(.008,.083,.095),'Dark',.001)
        # Integrated low optic: bridge frame and protected tinted lens.
        box('Optic',(.12,0,.239),(.15,.077,.018),'Dark')
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


if __name__=='__main__':build_hound()
