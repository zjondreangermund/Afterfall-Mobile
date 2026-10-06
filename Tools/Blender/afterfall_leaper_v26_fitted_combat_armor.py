"""Afterfall V26 fitted combat armor. Run in Object Mode on a saved scene copy.

Preserves existing rig/actions/face geometry/gameplay materials. Hides superseded
armor instead of deleting it. Rerun replaces only V26-generated meshes. Does not
save or export. Decorative material slots change; weak-point/signal slots do not.
"""
import bpy
import math
from mathutils import Vector, Matrix

VERSION = '2.6'
TAG = 'AfterfallRobotDetailPass'
COLLECTION = 'LEAPER_V26_CombatArmor'
LEGS = ('FL', 'FR', 'RL', 'RR')
PROTECTED = ('weak', 'wp_', 'signal', 'scan', 'alert', 'attack', 'sensor', 'glow')


def owned(o, rig):
    return any(m.type == 'ARMATURE' and m.object == rig for m in o.modifiers)


def mat(key):
    name = 'AF_V26_' + key
    old = bpy.data.materials.get(name)
    if old:
        return old
    colors = {'Armor':(.055,.065,.072), 'Edge':(.11,.125,.135),
              'Frame':(.022,.029,.034), 'Steel':(.23,.25,.26),
              'Cable':(.012,.014,.017), 'Orange':(.29,.078,.012)}
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*colors[key], 1)
    tree = m.node_tree
    p = tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*colors[key], 1)
    p.inputs['Metallic'].default_value = .86 if key != 'Cable' else .05
    p.inputs['Roughness'].default_value = .36 if key != 'Cable' else .65
    if key in ('Armor', 'Edge', 'Frame'):
        noise = tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 18
        noise.inputs['Detail'].default_value = 3
        ramp = tree.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = .65
        ramp.color_ramp.elements[1].position = .80
        tree.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
        mix = tree.nodes.new('ShaderNodeMixRGB')
        mix.inputs[1].default_value = (*colors[key], 1)
        mix.inputs[2].default_value = (.16,.054,.018,1)
        tree.links.new(ramp.outputs['Color'], mix.inputs[0])
        tree.links.new(mix.outputs[0], p.inputs['Base Color'])
        rough = tree.nodes.new('ShaderNodeMapRange')
        rough.inputs['To Min'].default_value = .34
        rough.inputs['To Max'].default_value = .72
        tree.links.new(ramp.outputs['Color'], rough.inputs['Value'])
        tree.links.new(rough.outputs['Result'], p.inputs['Roughness'])
    return m


class Builder:
    def __init__(self, rig, collection):
        self.rig, self.collection, self.parts = rig, collection, []

    def mesh(self, name, verts, faces, key, bone):
        data = bpy.data.meshes.new(name)
        data.from_pydata(verts, [], faces)
        data.update()
        o = bpy.data.objects.new(name, data)
        self.collection.objects.link(o)
        o[TAG] = VERSION
        o['AfterfallAttachmentBone'] = bone
        o.parent = self.rig
        o.matrix_parent_inverse = Matrix.Identity(4)
        vg = o.vertex_groups.new(name=bone)
        vg.add(list(range(len(verts))), 1, 'REPLACE')
        mod = o.modifiers.new('Existing skeleton', 'ARMATURE')
        mod.object = self.rig
        data.materials.append(mat(key))
        self.parts.append(o)
        return o

    def shell(self, name, a, b, side, up, rings, key, bone):
        # Each ring: distance along segment, half width, lower and upper height.
        a,b,side,up = map(Vector,(a,b,side,up))
        verts=[]
        for t,w,low,high in rings:
            c=a+(b-a)*t
            for x,z in ((-.68,low),(.68,low),(1,low*.6),(1,high*.6),
                        (.68,high),(-.68,high),(-1,high*.6),(-1,low*.6)):
                verts.append(c+side*(x*w)+up*z)
        faces=[tuple(reversed(range(8))),tuple(range(len(verts)-8,len(verts)))]
        for r in range(len(rings)-1):
            for i in range(8):
                j=(i+1)%8
                faces.append((r*8+i,r*8+j,(r+1)*8+j,(r+1)*8+i))
        return self.mesh(name,verts,faces,key,bone)

    def rod(self,name,a,b,r,key,bone,n=12):
        a,b=Vector(a),Vector(b)
        d=(b-a).normalized()
        ref=Vector((0,0,1)) if abs(d.z)<.9 else Vector((0,1,0))
        u=d.cross(ref).normalized(); v=d.cross(u).normalized()
        verts=[p+r*(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n)) for p in (a,b) for i in range(n)]
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        return self.mesh(name,verts,faces,key,bone)


def apply_armor():
    rig=bpy.data.objects.get('ARM_Leaper_Final')
    if not rig or rig.type!='ARMATURE' or bpy.context.mode!='OBJECT':
        raise RuntimeError('Open the current Leaper scene and switch to Object Mode.')
    if rig.library or rig.override_library or rig.data.library:
        raise RuntimeError('Use an editable local rig.')
    required={'body'} | {leg+'_'+p for leg in LEGS for p in ('upper','lower','foot')}
    if not required <= set(rig.data.bones.keys()):
        raise RuntimeError('The expected existing Leaper bones are missing.')
    if any(rig.data.bones[n].length < .001 or not rig.data.bones[n].use_deform for n in required):
        raise RuntimeError('Expected nonzero deform bones; no changes made.')
    frame,sub=bpy.context.scene.frame_current,bpy.context.scene.frame_subframe
    pose=rig.data.pose_position
    stage=bpy.data.collections.new(COLLECTION+'_Staging')
    bpy.context.scene.collection.children.link(stage)
    builder=Builder(rig,stage)
    old=[o for o in bpy.context.scene.objects if owned(o,rig) and o.get(TAG)==VERSION]
    try:
        rig.data.pose_position='REST'
        bpy.context.view_layer.update()
        for leg in LEGS:
            for part in ('upper','lower'):
                bone=leg+'_'+part
                bd=rig.data.bones[bone]
                a,b=bd.head_local.copy(),bd.tail_local.copy()
                axis=(b-a).normalized()
                side=axis.cross(Vector((0,0,1))).normalized()
                up=side.cross(axis).normalized()
                length=(b-a).length
                w=length*(.19 if part=='upper' else .155)
                h=w*.77
                profile=[(.13,w*.63,-h*.65,h*.65),(.26,w,-h*.7,h),
                         (.64,w*.92,-h*.7,h*.86),(.86,w*.45,-h*.4,h*.40)]
                builder.shell('V26_'+bone+'_Shell',a,b,side,up,profile,'Armor',bone)
                # Two separate outer plates leave a readable service seam.
                for i,(start,end,wide) in enumerate(((.27,.49,.80),(.515,.68,.69))):
                    builder.shell('V26_'+bone+'_Layer'+str(i),a+up*h*.86,b+up*h*.86,side,up,
                                  [(start,w*wide,0,.025),(end,w*wide*.86,0,.025)],'Edge',bone)
                # Internal spars connect both hinge centers underneath the armor.
                for sign in (-1,1):
                    off=side*sign*w*.48-up*h*.62
                    builder.rod('V26_'+bone+'_Spar'+str(sign),a+off,b+off,w*.13,'Frame',bone)
                # Compact actuator seats in two brackets on the outer shell.
                s=1 if side.y*(1 if leg.endswith('L') else -1)>0 else -1
                off=side*s*w*.93-up*h*.25
                p=a+(b-a)*.29+off; q=a+(b-a)*.65+off
                for i,pt in enumerate((p,q)):
                    builder.rod('V26_'+bone+'_Mount'+str(i),pt-side*s*w*.27,pt+side*s*.015,.037,'Edge',bone)
                builder.rod('V26_'+bone+'_Cylinder',p,p+(q-p)*.62,.030,'Frame',bone)
                builder.rod('V26_'+bone+'_Piston',p+(q-p)*.55,q,.016,'Steel',bone)
                builder.rod('V26_'+bone+'_Seal',p+(q-p)*.57,p+(q-p)*.65,.033,'Orange',bone)
                # Supported cable lies on inner side, with both ends embedded.
                off=-side*s*w*.88-up*h*.05
                points=[a+(b-a)*t+off+up*rise for t,rise in ((.25,0),(.34,.014),(.58,.014),(.68,0))]
                for i in range(3):
                    builder.rod('V26_'+bone+'_Cable'+str(i),points[i],points[i+1],.012,'Cable',bone)
                for i in (0,3):
                    builder.rod('V26_'+bone+'_CableSeat'+str(i),points[i]+side*s*.035,points[i],.023,'Edge',bone)
            # Replace decorative ball joints with compact concentric servo drums.
            for label,bone,p,r in (('Hip',leg+'_upper',rig.data.bones[leg+'_upper'].head_local,.18),
                                   ('Knee',leg+'_upper',rig.data.bones[leg+'_upper'].tail_local,.165),
                                   ('Ankle',leg+'_lower',rig.data.bones[leg+'_lower'].tail_local,.115)):
                axis=(rig.data.bones[bone].tail_local-rig.data.bones[bone].head_local).normalized()
                side=axis.cross(Vector((0,0,1))).normalized()
                builder.rod('V26_'+leg+label+'_Housing',p-side*r*.58,p+side*r*.58,r,'Frame',bone,16)
                for s in (-1,1):
                    c=p+side*s*r*.58
                    builder.rod('V26_'+leg+label+'_Rim'+str(s),c,c+side*s*.025,r*.88,'Edge',bone,16)
                    builder.rod('V26_'+leg+label+'_Axle'+str(s),c+side*s*.026,c+side*s*.040,r*.47,'Steel',bone,12)
        # Low faceted thorax replaces the ball and rectangular dorsal box.
        a=Vector((-.56,0,2.49)); b=Vector((.32,0,2.49))
        builder.shell('V26_Thorax',a,b,(0,1,0),(0,0,1),
                      [(0,.20,-.19,.12),(.23,.41,-.24,.24),(.64,.40,-.23,.20),(1,.20,-.10,.04)],'Armor','body')
        for s in (-1,1):
            builder.shell('V26_DorsalPlate'+str(s),a+Vector((0,s*.16,.23)),b+Vector((0,s*.16,.12)),
                          (0,1,0),(0,0,1),[(.17,.115,0,.025),(.67,.115,0,.025)],'Edge','body')
            for i in range(5):
                x=-.32+i*.058
                z=2.745-.11*((x+.56)/.88)+.003
                builder.rod('V26_Vent'+str(s)+'_'+str(i),(x,s*.10,z),(x,s*.22,z),.011,'Frame','body',4)
        # Commit only after all geometry has been generated successfully.
        for o in old:
            mesh=o.data
            bpy.data.objects.remove(o,do_unlink=True)
            if mesh.users==0: bpy.data.meshes.remove(mesh)
        for o in bpy.context.scene.objects:
            if o in builder.parts or not owned(o,rig): continue
            legacy=o.name in {'Core_Body','TopArmor','BackArmor','Armor_L','Armor_R','V15_DorsalBlade_0','V15_DorsalBlade_1'}
            legacy |= any(o.name in {leg+'_'+p for p in ('UpperArmor','LowerArmor','HipJoint','KneeJoint','AnkleJoint')} or o.name.startswith('FinalPlate_'+leg+'_') for leg in LEGS)
            legacy |= o.get(TAG)=='2.5' or (o.get(TAG)=='2.4' and any(o.name.startswith('V24_'+leg+'_') for leg in LEGS))
            legacy |= o.get(TAG)=='2.4' and o.name.startswith(('V24_TopArmor_','V24_BackArmor_'))
            if legacy:
                if 'V26_PreviousHideRender' not in o:
                    o['V26_PreviousHideRender']=o.hide_render
                    o['V26_PreviousHideViewport']=o.hide_viewport
                o.hide_render=True; o.hide_viewport=True
            # Keep all gameplay names and shaders. Darken decorative parts only.
            for slot in o.material_slots:
                if not slot.material: continue
                name=slot.material.name.lower()
                if any(t in name for t in PROTECTED): continue
                if any(t in name for t in ('titanium','blackarmor','obsidian','graphite','carapace')):
                    slot.link='OBJECT'; slot.material=mat('Armor')
                elif any(t in name for t in ('steel','chrome')):
                    slot.link='OBJECT'; slot.material=mat('Steel')
                elif any(t in name for t in ('frame','mechanic','gunmetal','inner')):
                    slot.link='OBJECT'; slot.material=mat('Frame')
        target=bpy.data.collections.get(COLLECTION)
        if target:
            for o in list(stage.objects):
                target.objects.link(o); stage.objects.unlink(o)
            bpy.data.collections.remove(stage)
        else: stage.name=COLLECTION
        for o in builder.parts:
            # Remove numeric suffixes left while rebuilding previous V26 objects.
            if o.name[-4:-3]=='.' and o.name[-3:].isdigit(): o.name=o.name[:-4]
        print('V26 complete:',len(builder.parts),'parts. Rig/actions preserved. Save As a new file.')
        return builder.parts
    except Exception:
        for o in builder.parts:
            if bpy.data.objects.get(o.name)==o:
                data=o.data; bpy.data.objects.remove(o,do_unlink=True)
                if data.users==0: bpy.data.meshes.remove(data)
        if bpy.data.collections.get(stage.name)==stage: bpy.data.collections.remove(stage)
        raise
    finally:
        rig.data.pose_position=pose
        bpy.context.scene.frame_set(frame,subframe=sub)
        bpy.context.view_layer.update()


if __name__=='__main__':
    apply_armor()
