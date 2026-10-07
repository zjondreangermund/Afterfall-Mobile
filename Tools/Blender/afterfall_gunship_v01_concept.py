"""Afterfall concept B gunship. Run in Blender Text Editor, Object Mode.
Meters; +X nose, +Z up. Replaces only this script's tagged collection output.
Separate fans animate; no save/export or scene-wide deletion. Blender 4.2+.
"""
import bpy
import math
from mathutils import Vector

TAG = 'AfterfallConceptGunship'

def build_gunship():
    if bpy.context.mode != 'OBJECT':
        raise RuntimeError('Switch to Object Mode first')
    old = [o for o in bpy.context.scene.objects if o.get(TAG)]
    col = bpy.data.collections.new('AF_GUNSHIP_V01')
    bpy.context.scene.collection.children.link(col)
    def empty(name, loc=(0,0,0), parent=None):
        o=bpy.data.objects.new(name,None);col.objects.link(o)
        o.location=loc;o.parent=parent;o[TAG]=True;return o
    root=empty('AF_GUNSHIP_ROOT')
    root['Reference']='Concept board B: twin ducted fans, paired pods, recessed sensor'
    root['Units']='meters; +X forward; +Z up'
    def mat(name,color,metal=.85,rough=.4,glow=0):
        m=bpy.data.materials.get('AF_GS_'+name) or bpy.data.materials.new('AF_GS_'+name)
        m.use_nodes=True;m.diffuse_color=(*color,1)
        n=m.node_tree.nodes;n.clear();l=m.node_tree.links
        p=n.new('ShaderNodeBsdfPrincipled');out=n.new('ShaderNodeOutputMaterial')
        l.new(p.outputs['BSDF'],out.inputs['Surface'])
        p.inputs['Base Color'].default_value=(*color,1)
        p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
        p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=glow
        if not glow:
            noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=90
            ramp=n.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].position=.69;ramp.color_ramp.elements[0].color=(*color,1)
            ramp.color_ramp.elements[1].position=.83;ramp.color_ramp.elements[1].color=(.15,.052,.018,1)
            l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
            bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.0003
            l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
        return m
    mats={'armor':mat('Armor',(.065,.072,.075)), 'edge':mat('WornMetal',(.22,.23,.22)),
          'dark':mat('Recess',(.015,.019,.022)), 'orange':mat('ServicePaint',(.48,.13,.023),.35),
          'sensor':mat('Sensor',(.95,.12,.006),.2,.2,2)}
    def adopt(o,name,key='armor',parent=root):
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o);o.name=name;o[TAG]=True;o.data.materials.append(mats[key])
        o.parent=parent
        return o
    def bevel(o,width=.018):
        b=o.modifiers.new('Machined edges','BEVEL');b.width=width;b.segments=3
        n=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
        return o
    def box(name,loc,size,key='armor'):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        o=adopt(bpy.context.object,name,key);o.dimensions=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        return bevel(o,min(size)*.14)
    def cylinder(name,a,b,r,key='edge',vertices=32):
        a,b=Vector(a),Vector(b)
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=(b-a).length,location=(a+b)/2)
        o=adopt(bpy.context.object,name,key);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
        for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
        return bevel(o,r*.07)
    def shell(name,sections,key='armor'):
        # Eight-sided loft; section is x, half-width, half-height, center-z.
        verts=[]
        profile=[(-.72,-1),(.72,-1),(1,-.55),(1,.55),(.72,1),(-.72,1),(-1,.55),(-1,-.55)]
        for x,w,h,z in sections:
            verts.extend((x,y*w,z+v*h) for y,v in profile)
        faces=[tuple(reversed(range(8)))]
        for j in range(len(sections)-1):
            for i in range(8):faces.append((j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i))
        faces.append(tuple(range((len(sections)-1)*8,len(sections)*8)))
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
        o=bpy.data.objects.new(name,mesh);col.objects.link(o);adopt(o,name,key);return bevel(o)
    def ring(name,loc,radius,width,height,key='armor'):
        # Actual hollow annular duct, not a solid disk or decorative torus.
        verts=[];N=64
        for z,r in [(-height/2,radius),(-height/2,radius-width),(height/2,radius),(height/2,radius-width)]:
            verts.extend((loc[0]+r*math.cos(i*2*math.pi/N),loc[1]+r*math.sin(i*2*math.pi/N),loc[2]+z) for i in range(N))
        faces=[]
        for i in range(N):
            j=(i+1)%N
            faces.extend([(i,j,2*N+j,2*N+i),(N+j,N+i,3*N+i,3*N+j),(2*N+i,2*N+j,3*N+j,3*N+i),(j,i,N+i,N+j)])
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
        o=bpy.data.objects.new(name,mesh);col.objects.link(o);adopt(o,name,key)
        return bevel(o,.012)
    try:
        shell('Central armored hull',[(-1.05,.24,.18,.05),(-.7,.46,.29,.08),(.15,.48,.32,.08),(.78,.31,.24,-.04),(1.03,.23,.19,-.1)])
        shell('Dorsal spine',[(-.8,.14,.06,.38),(-.25,.19,.09,.43),(.45,.16,.08,.34),(.79,.09,.035,.20)],'edge')
        box('Belly mechanical keel',(-.05,0,-.28),(1.2,.4,.2),'dark')
        for s in (-1,1):
            y=s*1.12
            cylinder('Fan support',(-.32,s*.35,.17),(-.32,y,.28),.10,'dark')
            cylinder('Support brace',(.37,s*.38,.11),(-.1,y,.23),.065)
            ring('Armored fan duct',(-.3,y,.35),.66,.11,.20)
            ring('Inner worn lip',(-.3,y,.46),.564,.018,.025,'edge')
            cylinder('Motor hub',(-.3,y,.19),(-.3,y,.43),.135,'dark')
            rotor=empty('Rotor_L' if s<0 else 'Rotor_R',(-.3,y,.34),root)
            for i in range(7):
                ang=i*2*math.pi/7
                o=box('Rotor blade',(-.3+.33*math.cos(ang),y+.33*math.sin(ang),.34),(.43,.105,.025),'edge')
                o.rotation_euler=(0,.12,ang+.2)
                world=o.matrix_world.copy();o.parent=rotor
                bpy.context.view_layer.update();o.matrix_world=world
            rotor.rotation_euler.z=0;rotor.keyframe_insert(data_path='rotation_euler',frame=1,index=2)
            rotor.rotation_euler.z=s*math.tau*20;rotor.keyframe_insert(data_path='rotation_euler',frame=120,index=2)
            # Pods remain visibly connected to substantial pivot supports.
            cylinder('Pod trunnion',(.2,s*.35,-.15),(.2,s*.65,-.34),.12,'dark')
            shell('Weapon pod',[(-.45,.19,.17,-.4),(.18,.22,.21,-.4),(.59,.17,.14,-.42)],'armor').location.y=s*.66
            for dy in (-.072,.072):
                cylinder('Protected barrel',(.3,s*.66+dy,-.42),(1.12,s*.66+dy,-.42),.047,'dark')
                cylinder('Muzzle collar',(1.02,s*.66+dy,-.42),(1.16,s*.66+dy,-.42),.06)
                cylinder('Dark muzzle inset',(1.158,s*.66+dy,-.42),(1.162,s*.66+dy,-.42),.041,'dark')
            for x in (-.3,-.02,.26):
                box('Pod service rib',(x,s*.855,-.4),(.035,.022,.23),'edge')
            box('Orange pod badge',(.25,s*.876,-.36),(.12,.009,.075),'orange')
            for x in (-.65,-.3,.12,.48):
                cylinder('Hull fastener',(x,s*.458,.12),(x,s*.473,.12),.022,'edge',8)
            for i in range(5):
                box('Cooling vent',(-.58+i*.075,s*.44,.23),(.025,.035,.105),'dark')
            box('Service stripe',(.38,s*.327,.255),(.30,.035,.018),'orange')
        cylinder('Recessed sensor surround',(.83,0,-.1),(1.095,0,-.1),.19,'dark')
        cylinder('Sensor rim',(1.06,0,-.1),(1.11,0,-.1),.145,'edge')
        cylinder('Sensor glass',(1.111,0,-.1),(1.115,0,-.1),.107,'sensor')
        box('Sensor upper brow',(.99,0,.055),(.33,.38,.06))
        for y in (-.16,.16):
            cylinder('Belly hydraulic',(-.38,y,-.27),(.37,y,-.36),.034,'edge')
        for name,loc in [('Muzzle_L',(1.16,-.66,-.42)),('Muzzle_R',(1.16,.66,-.42)),('Sensor',(1.12,0,-.1))]:
            e=empty('SOCKET_'+name,loc,root);e.empty_display_size=.08
        for o in old:bpy.data.objects.remove(o,do_unlink=True)
        bpy.context.scene.frame_set(1)
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':area.spaces.active.shading.type='MATERIAL'
        print('Gunship built. Save As a new .blend. Procedural materials require baking for Unreal.')
        return root
    except Exception:
        for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(col)
        raise

"""Run in an existing concept gunship scene. No geometry is deleted.
State preview: select AF_GUNSHIP_ROOT > Custom Properties > RigState:
0 patrol (white), 1 investigating (yellow), 2 combat (red).
Thruster hit preview: ThrusterHit_L / ThrusterHit_R, range 0 to 1.
Blender preview drivers/metadata require explicit Unreal material and hitbox setup.
"""
import bpy
from mathutils import Vector

TAG = 'AfterfallConceptGunship'

def set_driver(socket, index, root, prop, expression):
    socket.driver_remove('default_value', index)
    curve=socket.driver_add('default_value', index)
    d=curve.driver;d.type='SCRIPTED'
    v=d.variables.new();v.name='value';v.type='SINGLE_PROP'
    v.targets[0].id=root;v.targets[0].data_path='["'+prop+'"]'
    d.expression=expression

def apply_combat_visuals():
    roots=[o for o in bpy.context.scene.objects if o.get(TAG) and o.name.startswith('AF_GUNSHIP_ROOT')]
    if not roots:raise RuntimeError('Run the gunship generator first.')
    root=roots[0]
    root['RigState']=int(root.get('RigState',0))
    root.id_properties_ui('RigState').update(min=0,max=2,description='0 white patrol; 1 yellow investigating; 2 red combat')
    targets=[o for o in bpy.context.scene.objects if o.get(TAG)]
    sensor=next((o for o in targets if o.name.startswith('Sensor glass')),None)
    if not sensor:raise RuntimeError('Gunship sensor glass not found.')
    m=bpy.data.materials.get('AF_GS_StateSensor') or bpy.data.materials.new('AF_GS_StateSensor')
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    colors=('1.0','1.0 if value < 0.5 else (0.65 if value < 1.5 else 0.015)','1.0 if value < 0.5 else 0.008')
    for field in ('Base Color','Emission Color'):
        for i,expr in enumerate(colors):set_driver(p.inputs[field],i,root,'RigState',expr)
    p.inputs['Emission Strength'].default_value=2
    p.inputs['Metallic'].default_value=.1;p.inputs['Roughness'].default_value=.22
    m.diffuse_color=(1,.92,.8,1)
    sensor.data.materials.clear();sensor.data.materials.append(m)
    for side in ('L','R'):
        prop='ThrusterHit_'+side
        root[prop]=float(root.get(prop,0))
        root.id_properties_ui(prop).update(min=0,max=1,description='Hit preview: grey to pale yellow-white')
        mat=bpy.data.materials.get('AF_GS_ThrusterWeak_'+side) or bpy.data.materials.new('AF_GS_ThrusterWeak_'+side)
        mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF')
        for field in ('Base Color','Emission Color'):
            for i,expr in enumerate(('0.25+0.75*value','0.27+0.67*value','0.29+0.41*value')):
                set_driver(p.inputs[field],i,root,prop,expr)
        p.inputs['Emission Strength'].driver_remove('default_value')
        d=p.inputs['Emission Strength'].driver_add('default_value').driver
        v=d.variables.new();v.name='value';v.type='SINGLE_PROP'
        v.targets[0].id=root;v.targets[0].data_path='["'+prop+'"]';d.expression='3*value'
        p.inputs['Metallic'].default_value=.7;p.inputs['Roughness'].default_value=.38
        mat.diffuse_color=(.25,.27,.29,1)
        for o in targets:
            if o.type!='MESH' or not o.name.startswith(('Motor hub','Inner worn lip','Armored fan duct')):continue
            center=o.matrix_world.translation
            # Duct vertices contain world-space coordinates in this generator.
            if o.name.startswith(('Inner worn lip','Armored fan duct')):
                center=o.matrix_world @ (sum((v.co for v in o.data.vertices),start=Vector())/len(o.data.vertices))
            object_side='L' if center.y<0 else 'R'
            if object_side!=side:continue
            o['WeakSpotId']='Thruster_'+side
            o['DamageRole']='ThrusterWeakSpot'
            o['HitPreviewProperty']=prop
            o['UnrealSetup']='Bind separate hitbox and damage response on import'
            o.data.materials.clear();o.data.materials.append(mat)
    root['WeakSpotIds']='Thruster_L, Thruster_R'
    root['SensorStates']='0 Patrol white | 1 Investigating yellow | 2 Combat red'
    bpy.context.view_layer.update()
    print('Thruster weak spots and state-driven sensor applied.')
    return root

if __name__=='__main__':
    build_gunship()
    apply_combat_visuals()
