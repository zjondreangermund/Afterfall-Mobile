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
    apply_combat_visuals()
