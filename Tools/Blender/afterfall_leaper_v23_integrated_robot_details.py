"""Afterfall Leaper v23 — integrated industrial details (Blender 5.2).
Open the existing final scene, Object Mode, Text Editor > Open > Run Script.
Does NOT save, export, change bones, actions, NLA, frame range or gameplay slots.
Only tagged v22/v23 details belonging to this rig are replaced, after staging.
See Docs/Enemies/Leaper_V23_Integrated_Robot.md for checks and limitations.
"""
import math
import bpy
from mathutils import Matrix, Vector

VERSION = '2.3'
OWNER_KEY = 'AfterfallRobotDetailPass'
COLLECTION = 'LEAPER_V23_IntegratedDetails'
LEGS = ('FL', 'FR', 'ML', 'MR', 'RL', 'RR')
PALETTE = {
    'Titanium': ((.145, .165, .185), .92, .38),
    'Steel': ((.285, .315, .345), .96, .30),
    'Frame': ((.075, .088, .102), .94, .42),
    'Chrome': ((.36, .39, .42), .98, .22),
    'Cable': ((.022, .026, .031), .05, .64),
    'Orange': ((.52, .12, .018), .65, .36),
}
# Only known decorative materials. Weak-point and signal slots are never remapped.
REMAP = {
    'LEAP_V17_Obsidian': 'Titanium', 'LEAP_V17_CarapaceEdge': 'Steel',
    'LEAP_V17_InnerMechanism': 'Frame', 'LEAP_FINAL_GraphiteArmor': 'Titanium',
    'LEAP_FINAL_MechanicalDark': 'Frame', 'M_Armor_BoneWhite': 'Steel',
    'M_Armor_DarkWhite': 'Titanium', 'M_Mechanical_Dark': 'Frame',
    'M_Hydraulic': 'Chrome', 'M_Accent_Orange': 'Orange', 'M_Cable': 'Cable',
    'AF_Metal_DarkTitanium': 'Titanium', 'AF_Metal_BrushedSteel': 'Steel',
    'AF_Metal_Gunmetal': 'Frame', 'AF_Metal_HydraulicSteel': 'Chrome',
    'AF_Robot_CableRubber': 'Cable', 'AF_Metal_ServiceOrange': 'Orange',
}


def belongs(obj, rig, root):
    parent = obj.parent
    while parent:
        if parent in (rig, root):
            return True
        parent = parent.parent
    return any(m.type == 'ARMATURE' and m.object == rig for m in obj.modifiers)


def remove_detail(obj):
    data = obj.data
    kind = obj.type
    bpy.data.objects.remove(obj, do_unlink=True)
    if data and data.users == 0:
        if kind == 'MESH':
            bpy.data.meshes.remove(data)
        elif kind == 'CURVE':
            bpy.data.curves.remove(data)


def material(key):
    name = 'AF_V23_' + key
    mat = bpy.data.materials.get(name)
    if mat:
        if mat.get(OWNER_KEY) != VERSION:
            raise RuntimeError('Material name is already used by another asset: ' + name)
        return mat  # preserve artist adjustments on rerun
    mat = bpy.data.materials.new(name)
    mat[OWNER_KEY] = VERSION
    mat.use_nodes = True
    color, metal, rough = PALETTE[key]
    node = mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = (*color, 1)
    node.inputs['Metallic'].default_value = metal
    node.inputs['Roughness'].default_value = rough
    node.inputs['Emission Strength'].default_value = 0
    if key in ('Steel', 'Chrome') and node.inputs.get('Anisotropic IOR Level'):
        node.inputs['Anisotropic IOR Level'].default_value = .28
    mat.diffuse_color = (*color, 1)
    return mat


class Builder:
    """Meshes authored in armature rest space, skinned to EXISTING bones."""
    def __init__(self, rig, collection, mats):
        self.rig, self.collection, self.mats = rig, collection, mats
        self.parts = []

    def mesh(self, name, vertices, faces, key, bone):
        data = bpy.data.meshes.new(name + '_Mesh')
        data.from_pydata(vertices, [], faces)
        data.update()
        obj = bpy.data.objects.new(name, data)
        self.collection.objects.link(obj)
        self.parts.append(obj)
        obj[OWNER_KEY] = VERSION
        obj['AfterfallDetailRig'] = self.rig.name
        obj['AfterfallIntendedName'] = name
        obj['AfterfallAttachmentBone'] = bone
        obj.parent = self.rig
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = Matrix.Identity(4)
        group = obj.vertex_groups.new(name=bone)
        group.add(list(range(len(vertices))), 1.0, 'REPLACE')
        mod = obj.modifiers.new('Existing Leaper skeleton', 'ARMATURE')
        mod.object = self.rig
        mod.use_bone_envelopes = False
        mod.use_vertex_groups = True
        data.materials.append(self.mats[key])
        obj.color = self.mats[key].diffuse_color
        return obj

    def tube(self, name, points, radius, key, bone, sides=10):
        points = [Vector(p) for p in points]
        if any((b-a).length < 1e-7 for a,b in zip(points, points[1:])):
            raise RuntimeError('Degenerate detail: ' + name)
        verts, faces = [], []
        # Parallel-transport frame avoids cable twist between adjacent sections.
        normal = None
        for i,p in enumerate(points):
            tangent = (points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
            if normal is None or abs(normal.dot(tangent)) > .98:
                ref = Vector((0,0,1)) if abs(tangent.z) < .85 else Vector((0,1,0))
                normal = tangent.cross(ref).normalized()
            else:
                normal = (normal-tangent*normal.dot(tangent)).normalized()
            second = tangent.cross(normal).normalized()
            for j in range(sides):
                a = math.tau*j/sides
                verts.append(p+radius*(normal*math.cos(a)+second*math.sin(a)))
        for i in range(len(points)-1):
            for j in range(sides):
                k=i*sides+j; n=i*sides+(j+1)%sides
                faces.append((k,n,n+sides,k+sides))
        faces.extend([tuple(reversed(range(sides))),
                      tuple((len(points)-1)*sides+j for j in range(sides))])
        return self.mesh(name, verts, faces, key, bone)

    def box(self, name, center, axes, half, key, bone):
        center=Vector(center)
        x,y,z=axes
        verts=[center+x*half[0]*a+y*half[1]*b+z*half[2]*c
               for a,b,c in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                             (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
        faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        return self.mesh(name, verts, faces, key, bone)

    def segment(self, bone_name, radius):
        bone=self.rig.data.bones[bone_name]
        a,b=bone.head_local.copy(),bone.tail_local.copy()
        d=b-a; axis=d.normalized()
        side=bone.matrix_local.to_3x3() @ Vector((1,0,0))
        side.normalize()
        normal=axis.cross(side).normalized()
        prefix='V23_'+bone_name
        # Load-bearing inner rail reaches both joints. Existing outer armor stays.
        self.tube(prefix+'_FrameRail', [a,b], radius*.62, 'Frame', bone_name)
        # Compact solid rotary housings, not open torus rings.
        for label,p in (('RootServo',a),('EndServo',b)):
            self.tube(prefix+'_'+label, [p-normal*radius*.42,p+normal*radius*.42],
                      radius, 'Steel', bone_name, 12)
            self.tube(prefix+'_'+label+'Cap', [p+normal*radius*.39,p+normal*radius*.51],
                      radius*.65, 'Frame', bone_name, 12)
            for j in range(3):
                angle=j*math.tau/3
                q=p+(side*math.cos(angle)+axis*math.sin(angle))*radius*.73
                self.tube(prefix+'_'+label+'Bolt'+str(j),
                          [q+normal*radius*.38,q+normal*radius*.52],
                          radius*.115,'Chrome',bone_name,6)
        # Sleeve/rod + end brackets run along one rigid segment: no joint-spanning
        # props and no new bones/constraints requiring a different UE skeleton.
        off=side*radius*.92
        start=a+d*.16+off; end=a+d*.84+off
        for i,p in enumerate((start,end)):
            self.tube(prefix+'_ActuatorMount'+str(i), [p-off,p],radius*.30,'Steel',bone_name)
        self.tube(prefix+'_Cylinder',[start,start+(end-start)*.62],radius*.35,'Titanium',bone_name)
        self.tube(prefix+'_PistonRod',[start+(end-start)*.56,end],radius*.18,'Chrome',bone_name)
        self.tube(prefix+'_RodSeal',[start+(end-start)*.58,start+(end-start)*.66],
                  radius*.37,'Frame',bone_name)
        # Two protected cable runs, endpoints physically enter metal glands.
        for j,shift in enumerate((-.20,.20)):
            cable_off=-side*radius*.88+normal*radius*shift
            p=a+d*.16+cable_off; q=a+d*.84+cable_off
            points=[p,p+d*.16-side*radius*.10,q-d*.16-side*radius*.10,q]
            self.tube(prefix+'_Cable'+str(j), points,radius*.105,'Cable',bone_name,8)
            for k,t in enumerate((.16,.50,.84)):
                anchor=a+d*t+cable_off
                self.tube(prefix+'_CableClamp'+str(j)+str(k),
                          [a+d*t,anchor],radius*.17,'Steel',bone_name,8)
        self.tube(prefix+'_ServiceStripe',[start+d*.06,start+d*.095],radius*.356,'Orange',bone_name)


def rigid_bone(obj, rig):
    if obj.parent == rig and obj.parent_type == 'BONE':
        return obj.parent_bone
    if not any(m.type == 'ARMATURE' and m.object == rig for m in obj.modifiers):
        return None
    used=set()
    names={g.index:g.name for g in obj.vertex_groups if g.name in rig.data.bones}
    for vertex in obj.data.vertices:
        weights=[g for g in vertex.groups if g.weight > .0001 and g.group in names]
        if len(weights)!=1 or abs(weights[0].weight-1) > .001:
            return None
        used.add(names[weights[0].group])
    return next(iter(used)) if len(used)==1 else None


def surface_patch(obj, rig):
    """Largest suitable triangle in REST geometry, not object origin/bounds.
    Returns an inscribed footprint so the entire panel sits on actual metal.
    """
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        matrix=rig.matrix_world.inverted() @ evaluated.matrix_world
        candidates=[]
        for tri in mesh.loop_triangles:
            a,b,c=[matrix @ mesh.vertices[i].co for i in tri.vertices]
            cross=(b-a).cross(c-a)
            if cross.length < 1e-9:
                continue
            normal=cross.normalized()
            if normal.z < .20:  # upper facing actual surface only
                continue
            ab,bc,ca=(a-b).length,(b-c).length,(c-a).length
            perimeter=ab+bc+ca
            radius=cross.length/perimeter
            center=(a*bc+b*ca+c*ab)/perimeter
            candidates.append((radius,center,normal,(b-a).normalized()))
        return max(candidates,key=lambda item:item[0]) if candidates else None
    finally:
        evaluated.to_mesh_clear()


def apply_details():
    root=bpy.data.objects.get('LEAPER_ROOT')
    rig=bpy.data.objects.get('ARM_Leaper_Final')
    if not root or not rig or rig.type!='ARMATURE':
        raise RuntimeError('Open the current final Leaper scene with ARM_Leaper_Final and LEAPER_ROOT first.')
    if bpy.context.mode!='OBJECT':
        raise RuntimeError('Switch to Object Mode, then Run Script again.')
    if root.library or rig.library or rig.data.library or root.override_library or rig.override_library:
        raise RuntimeError('Use a local editable Leaper rig. Linked/overridden rigs are left untouched.')
    required={'body','head'}
    legs=[]
    for leg in LEGS:
        present=[f'{leg}_{part}' in rig.data.bones for part in ('upper','lower','foot')]
        if any(present) and not all(present):
            raise RuntimeError('Incomplete leg chain: '+leg+'. No details changed.')
        if all(present):
            legs.append(leg)
            required.update(f'{leg}_{part}' for part in ('upper','lower','foot'))
    if len(legs)<4:
        raise RuntimeError('Expected at least four complete leg chains. No details changed.')
    missing=required-set(rig.data.bones.keys())
    if missing:
        raise RuntimeError('Missing bones: '+', '.join(sorted(missing)))
    if any(not rig.data.bones[n].use_deform or rig.data.bones[n].length<.0001 for n in required):
        raise RuntimeError('Attachment bones must be nonzero deform bones. Rig left untouched.')
    if abs(rig.matrix_world.determinant())<1e-9:
        raise RuntimeError('Rig has zero scale. No details changed.')
    owned=[o for o in bpy.context.scene.objects if belongs(o,rig,root)]
    # v22 never tagged the rig ID; restrict its cleanup to this root/rig hierarchy.
    old=[o for o in owned if o.get(OWNER_KEY) in ('2.2',VERSION) and o.type in ('MESH','CURVE')]
    source=[o for o in owned if o.type=='MESH' and o not in old and not o.hide_render and not o.hide_viewport]
    saved_pose=rig.data.pose_position
    stage=bpy.data.collections.new(COLLECTION+'_Staging')
    bpy.context.scene.collection.children.link(stage)
    builder=None
    warnings=[]
    material_ids={m.as_pointer() for m in bpy.data.materials}
    try:
        rig.data.pose_position='REST'
        bpy.context.view_layer.update()
        mats={key:material(key) for key in PALETTE}
        builder=Builder(rig,stage,mats)
        for leg in legs:
            upper=rig.data.bones[leg+'_upper']
            lower=rig.data.bones[leg+'_lower']
            # Derived locally per limb. Never infer size from the head/body origins.
            radius=min(upper.length,lower.length)*.058
            builder.segment(leg+'_upper',radius)
            builder.segment(leg+'_lower',radius*.82)
            foot=rig.data.bones[leg+'_foot']
            builder.tube('V23_'+leg+'_AnklePin',
                         [foot.head_local,foot.head_local+(foot.tail_local-foot.head_local)*.18],
                         radius*.67,'Frame',leg+'_foot')
        head=rig.data.bones['head']
        a=head.head_local.copy(); d=head.tail_local-a
        nr=min(head.length*.09, min(rig.data.bones[l+'_upper'].length for l in legs)*.05)
        builder.tube('V23_NeckSpindle',[a,a+d*.78],nr,'Frame','head')
        builder.tube('V23_NeckSocket',[a,a+d*.16],nr*1.45,'Steel','head')
        for j,sign in enumerate((-1,1)):
            off=(head.matrix_local.to_3x3() @ Vector((sign,0,0))).normalized()*nr*.8
            builder.tube('V23_NeckCable'+str(j),[a+off,a+d*.30+off*1.15,a+d*.65+off],
                         nr*.19,'Cable','head',8)
            for k,t in enumerate((.03,.63)):
                p=a+d*t
                builder.tube('V23_NeckGland'+str(j)+str(k),[p,p+off],nr*.32,'Steel','head',8)
        # Attach small plates only to proven rigid body meshes; mixed meshes skip.
        names=('Core_Body','Thorax_Core','Armor_Center','Rear_Housing')
        hosts=[o for name in names for o in source if o.name==name][:2]
        panels=0
        for obj in hosts:
            bone=rigid_bone(obj,rig)
            if not bone or not rig.data.bones[bone].use_deform or bone.startswith(('weak_','cover_')):
                warnings.append('Skipped service panel on '+obj.name+': attachment is not one rigid body bone.')
                continue
            patch=surface_patch(obj,rig)
            if not patch:
                warnings.append('Skipped service panel on '+obj.name+': no suitable metal surface.')
                continue
            radius,center,normal,x=patch
            radius=min(radius*.70,min(rig.data.bones[l+'_upper'].length for l in legs)*.13)
            y=normal.cross(x).normalized(); axes=(x,y,normal)
            prefix='V23_'+obj.name
            # Underside intersects the source by 1% of footprint: no hover gap.
            builder.box(prefix+'_ServicePlate',center+normal*radius*.035,axes,
                        (radius*.70,radius*.55,radius*.045),'Titanium',bone)
            builder.box(prefix+'_PanelSeam',center+normal*radius*.085,axes,
                        (radius*.55,radius*.37,radius*.01),'Frame',bone)
            for i in range(4):
                p=center+x*radius*(-.36+i*.24)+normal*radius*.11
                builder.box(prefix+'_Vent'+str(i),p,axes,
                            (radius*.055,radius*.32,radius*.026),'Steel',bone)
            for j,(sx,sy) in enumerate(((-1,-1),(-1,1),(1,-1),(1,1))):
                p=center+x*radius*.58*sx+y*radius*.43*sy
                builder.tube(prefix+'_Bolt'+str(j),[p+normal*radius*.07,p+normal*radius*.12],
                             radius*.047,'Chrome',bone,6)
            panels+=1
        if not panels:
            warnings.append('No suitable body panel host found; body panels skipped instead of guessed.')
        # Geometry staged successfully. Swap only generated objects; original
        # object pointers, modifiers, weights and animation data stay intact.
        target=bpy.data.collections.get(COLLECTION)
        if target and target.library:
            raise RuntimeError('Output collection is linked/read-only.')
        if target is None:
            target=bpy.data.collections.new(COLLECTION)
            bpy.context.scene.collection.children.link(target)
        elif target not in list(bpy.context.scene.collection.children_recursive):
            bpy.context.scene.collection.children.link(target)
        for obj in builder.parts:
            target.objects.link(obj)
            stage.objects.unlink(obj)
        for obj in old:
            remove_detail(obj)
        for obj in builder.parts:
            obj.name=obj['AfterfallIntendedName']
            obj.data.name=obj.name+'_Mesh'
        # Object-linked slot overrides avoid changing other objects sharing meshes
        # or materials. No slot is inserted/reordered; signal/weakpoint names stay.
        recolored=0
        for obj in source:
            if obj.library or obj.override_library:
                warnings.append('Skipped material overrides on linked object '+obj.name)
                continue
            for slot in obj.material_slots:
                mat=slot.material
                if mat and mat.name in REMAP:
                    slot.link='OBJECT'
                    slot.material=mats[REMAP[mat.name]]
                    recolored+=1
        root['RobotDetailVersion']=VERSION
        root['V23GeneratedCollection']=COLLECTION
        root['MachineSignalRule']='White scan; yellow alert; red attack (existing gameplay slots)'
        root['MachineWeakPointRule']='Grey dormant; pale yellow-white exposed/hit (existing slots)'
        root['V23ValidationNote']='Inspect actual scene animation and UE import before replacing production asset.'
        result={'parts':builder.parts,'legs':legs,'removed':len(old),'panels':panels,
                'recolored':recolored,'warnings':warnings}
    except Exception:
        if builder:
            for obj in list(builder.parts):
                if obj.name in bpy.data.objects:
                    remove_detail(obj)
        for mat in list(bpy.data.materials):
            if mat.as_pointer() not in material_ids and mat.users==0:
                bpy.data.materials.remove(mat)
        raise
    finally:
        rig.data.pose_position=saved_pose
        bpy.context.view_layer.update()
        bpy.data.collections.remove(stage)
    print('\nAFTERFALL V23 COMPLETE: %d mesh details, %d legs; %d old details replaced.' %
          (len(result['parts']),len(legs),len(old)))
    for warning in warnings:
        print('NOTE:',warning)
    print('Rig/actions retained. Save As a NEW .blend after playback checks.')
    return result


if __name__=='__main__':
    apply_details()
