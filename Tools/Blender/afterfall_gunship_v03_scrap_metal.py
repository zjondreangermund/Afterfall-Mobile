"""Run on the existing gunship in Object Mode. Adds scrap armor and fasteners.
Replaces only this patch's own tagged objects. Preserves sensor/weak-spot materials.
Procedural finish is Blender-only until baked for Unreal. Save As after review.
"""
import bpy
import math
import random
from mathutils import Vector

TAG='AfterfallGunshipScrap'

def apply_scrap_detail():
    if bpy.context.mode!='OBJECT':raise RuntimeError('Switch to Object Mode first.')
    root=next((o for o in bpy.context.scene.objects if o.get('AfterfallConceptGunship') and o.name.startswith('AF_GUNSHIP_ROOT')),None)
    if root is None:raise RuntimeError('Open the generated gunship first.')
    old=[o for o in bpy.context.scene.objects if o.get(TAG)]
    col=bpy.data.collections.new('AF_GUNSHIP_SCRAP');bpy.context.scene.collection.children.link(col)
    rng=random.Random(41)
    def material(name,color,rough=.55,metal=.8):
        m=bpy.data.materials.get('AF_SCRAP_'+name) or bpy.data.materials.new('AF_SCRAP_'+name)
        m.use_nodes=True;m.diffuse_color=(*color,1)
        n=m.node_tree.nodes;n.clear();l=m.node_tree.links
        p=n.new('ShaderNodeBsdfPrincipled');out=n.new('ShaderNodeOutputMaterial');l.new(p.outputs['BSDF'],out.inputs['Surface'])
        coord=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value=32;noise.inputs['Detail'].default_value=4
        l.new(coord.outputs['Object'],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.60
        ramp.color_ramp.elements[0].color=(*color,1);ramp.color_ramp.elements[1].position=.77
        ramp.color_ramp.elements[1].color=(.19,.064,.022,1)
        l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
        p.inputs['Metallic'].default_value=metal
        roughnode=n.new('ShaderNodeMapRange');roughnode.inputs['To Min'].default_value=rough-.1;roughnode.inputs['To Max'].default_value=min(.95,rough+.2)
        l.new(noise.outputs['Fac'],roughnode.inputs['Value']);l.new(roughnode.outputs['Result'],p.inputs['Roughness'])
        grain=n.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=280
        l.new(coord.outputs['Object'],grain.inputs['Vector'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.00045
        l.new(grain.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
        return m
    mats=[material('Blackened steel',(.035,.045,.052)),material('Salvaged galvanized',(.25,.28,.27),.46),
          material('Old brown steel',(.12,.09,.064)),material('Faded industrial paint',(.26,.082,.017),.64,.35)]
    boltmat=material('Fasteners',(.31,.32,.30),.42)
    weldmat=material('Weld metal',(.11,.12,.13),.62)
    dark=material('Screw recess',(.009,.012,.014),.6,.3)
    def adopt(o,name,mat):
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o);o.name=name;o[TAG]=True;o['AfterfallConceptGunship']=True
        o.data.materials.append(mat);o.parent=root
        return o
    def cylinder(name,pos,normal,r,depth,mat,vertices=12):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=pos)
        o=adopt(bpy.context.object,name,mat);o.rotation_euler=Vector(normal).to_track_quat('Z','Y').to_euler()
        b=o.modifiers.new('Small edge bevel','BEVEL');b.width=.001;b.segments=2
        return o
    def fastener(pos,normal,screw=False):
        pos=Vector(pos);normal=Vector(normal).normalized()
        cylinder('Fastener washer',pos+normal*.001,normal,.016,.003,boltmat,24)
        cylinder('Slotted screw' if screw else 'Hex bolt',pos+normal*.007,normal,.010,.010,boltmat,24 if screw else 6)
        if screw:
            # Physical black slot sits on the screw face.
            tangent=normal.cross(Vector((1,0,0)))
            if tangent.length<.1:tangent=normal.cross(Vector((0,1,0)))
            tangent.normalize()
            a=pos+normal*.0125-tangent*.006;b=pos+normal*.0125+tangent*.006
            cylinder('Screwdriver slot',(a+b)/2,b-a,.0013,(b-a).length,dark,8)
    def plate(name,points,normal,mat):
        normal=Vector(normal).normalized();points=[Vector(p) for p in points];thickness=.008
        verts=[tuple(p+normal*d) for d in (0,thickness) for p in points];N=len(points)
        faces=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
        o=bpy.data.objects.new(name,mesh);col.objects.link(o);adopt(o,name,mat)
        b=o.modifiers.new('Worn plate edges','BEVEL');b.width=.002;b.segments=2
        center=sum(points,Vector())/N
        for i,p in enumerate(points):fastener(p.lerp(center,.18)+normal*thickness,normal,i%2==0)
        return o
    def weld(a,b,normal):
        a,b=Vector(a),Vector(b);normal=Vector(normal)
        count=max(2,int((b-a).length/.013))
        for i in range(count):
            pos=a.lerp(b,i/(count-1))+normal*.002
            bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=.005,location=pos)
            o=adopt(bpy.context.object,'Uneven weld bead',weldmat);o.scale=(1.3,1,.65+rng.random()*.3)
    try:
        # Top panels fitted to the existing octagonal hull's flat roof.
        for x0,x1,z0,z1,width in [(-.66,-.36,.374,.396,.27),(-.32,.08,.399,.407,.28),(.18,.48,.395,.328,.19),(.5,.72,.323,.226,.15)]:
            for s in (-1,1):
                pts=[(x0,s*.035,z0),(x1,s*.035,z1),(x1-.025,s*width,z1),(x0+.025,s*width,z0)]
                normal=Vector((z0-z1,0,x1-x0)).normalized()
                plate('Overlapping salvaged roof plate',pts,normal,mats[rng.randrange(4)])
                weld(pts[0],pts[1],normal)
        # Side armor sits just outside the hull; different patches on each side.
        for s in (-1,1):
            for x0,x1,y,z in [(-.62,-.37,.466,.09),(-.32,-.04,.486,.05),(.02,.26,.485,.04)]:
                pts=[(x0,s*y,z-.09),(x1,s*y,z-.08),(x1-.018,s*y,z+.10),(x0+.028,s*y,z+.10)]
                plate('Riveted hull repair patch',pts,(0,s,0),mats[rng.randrange(4)])
                weld(pts[0],pts[1],(0,s,0))
            # Repairs and clamps on the pod sides.
            for x0,x1 in [(-.36,-.13),(-.08,.13),(.19,.39)]:
                pts=[(x0,s*.889,-.49),(x1,s*.889,-.49),(x1-.02,s*.889,-.31),(x0+.01,s*.889,-.30)]
                plate('Weapon pod scrap plate',pts,(0,s,0),mats[rng.randrange(4)])
            # Short ring segments: leave motor hubs and inner weak-spot lip visible.
            cy=s*1.12
            for k in range(8):
                a=k*math.tau/8+.025;b=a+.34
                pts=[(-.3+r*math.cos(t),cy+r*math.sin(t),.456) for r,t in [(.58,a),(.647,a),(.647,b),(.58,b)]]
                plate('Bolted fan rim repair',pts,(0,0,1),mats[k%3])
            # Straps wrap the exterior duct wall with actual bolt heads.
            for k in range(6):
                a=k*math.tau/6
                pos=Vector((-.3+.665*math.cos(a),cy+.665*math.sin(a),.35))
                normal=Vector((math.cos(a),math.sin(a),0));tangent=Vector((-math.sin(a),math.cos(a),0))
                pts=[pos+tangent*u+Vector((0,0,z)) for u,z in [(-.028,-.075),(.028,-.075),(.028,.075),(-.028,.075)]]
                plate('Salvaged duct reinforcement strap',pts,normal,mats[1])
        for o in old:bpy.data.objects.remove(o,do_unlink=True)
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':area.spaces.active.shading.type='MATERIAL'
        root['ArtFinish']='Salvaged plates, exposed hex bolts, slotted screws, weld seams'
        print('Scrap-metal detail added. Sensor and weak-spot drivers preserved. Save As.')
    except Exception:
        for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(col);raise

if __name__=='__main__':
    apply_scrap_detail()
