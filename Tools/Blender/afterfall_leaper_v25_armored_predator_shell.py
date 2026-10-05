"""Afterfall Leaper V25 — EXPERIMENTAL armored predator shell pass.

Run on Leaper_Standard_V24_Fitted.blend or the current final Leaper scene.
Adds the heavy angular armor language from the supplied reference image while
preserving the existing alien/predator face, rig, weak points, actions and NLA.

Blender 5.2.2 preservation and attachment checks passed on the V24 scene.
This is an armor-fit preview, not the final reference match. Test a scene copy.
Only V25-owned objects are replaced. The script does not save or export.
Save As a new .blend after inspection.
"""
import math
import bpy
from mathutils import Matrix, Vector

VERSION = "2.5"
OWNER = "AfterfallRobotDetailPass"
COLLECTION_NAME = "LEAPER_V25_ArmoredPredator"
LEGS = ("FL", "FR", "RL", "RR")

PALETTE = {
    "Armor": ((0.055, 0.068, 0.082), 0.88, 0.40),
    "ArmorEdge": ((0.16, 0.19, 0.22), 0.92, 0.31),
    "Inner": ((0.026, 0.032, 0.040), 0.82, 0.49),
    "Bearing": ((0.22, 0.25, 0.28), 0.95, 0.27),
    "RustAccent": ((0.26, 0.075, 0.018), 0.72, 0.42),
}


def material(key):
    # Reuse the artist's latest weathered finish without editing its nodes.
    aliases = {
        "Armor": ("AF_Metal_DarkTitanium", "AF_V24_Titanium", "LEAP_FINAL_BlackArmor"),
        "ArmorEdge": ("AF_Metal_BrushedSteel", "AF_V24_Steel", "LEAP_FINAL_JointSteel"),
        "Bearing": ("AF_Metal_BrushedSteel", "LEAP_FINAL_JointSteel"),
        "Inner": ("AF_Metal_Gunmetal", "LEAP_FINAL_MechanicalDark"),
        "RustAccent": ("AF_Metal_ServiceOrange",),
    }
    for alias in aliases.get(key, ()):
        existing = bpy.data.materials.get(alias)
        if existing:
            return existing
    name = "AF_V25_" + key
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat[OWNER] = VERSION
    mat.use_nodes = True
    node = mat.node_tree.nodes.get("Principled BSDF")
    base, metallic, rough = PALETTE[key]
    node.inputs["Base Color"].default_value = (*base, 1.0)
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = rough
    node.inputs["Emission Strength"].default_value = 0.0
    mat.diffuse_color = (*base, 1.0)
    return mat


def belongs(obj, rig, root):
    p = obj.parent
    while p:
        if p in (rig, root):
            return True
        p = p.parent
    return any(m.type == "ARMATURE" and m.object == rig for m in obj.modifiers)


def remove_owned(obj):
    data = obj.data
    kind = obj.type
    bpy.data.objects.remove(obj, do_unlink=True)
    if data and data.users == 0:
        if kind == "MESH":
            bpy.data.meshes.remove(data)
        elif kind == "CURVE":
            bpy.data.curves.remove(data)


class Builder:
    def __init__(self, rig, collection, mats):
        self.rig = rig
        self.collection = collection
        self.mats = mats
        self.parts = []

    def mesh(self, name, verts, faces, key, bone):
        data = bpy.data.meshes.new(name + "_Mesh")
        data.from_pydata(verts, [], faces)
        data.update()
        obj = bpy.data.objects.new(name, data)
        self.collection.objects.link(obj)
        obj[OWNER] = VERSION
        obj["AfterfallDetailRig"] = self.rig.name
        obj["AfterfallAttachmentBone"] = bone
        obj.parent = self.rig
        obj.matrix_parent_inverse = Matrix.Identity(4)
        group = obj.vertex_groups.new(name=bone)
        group.add(list(range(len(verts))), 1.0, "REPLACE")
        mod = obj.modifiers.new("Existing Leaper skeleton", "ARMATURE")
        mod.object = self.rig
        mod.use_vertex_groups = True
        mod.use_bone_envelopes = False
        data.materials.append(self.mats[key])
        self.parts.append(obj)
        return obj

    def prism(self, name, a, b, side, up, width_a, width_b, height, key, bone, offset=0.0):
        """Tapered angular armor plate around one existing rigid bone."""
        a, b = Vector(a), Vector(b)
        axis = (b - a).normalized()
        side = Vector(side).normalized()
        up = Vector(up).normalized()
        if abs(axis.dot(side)) > .001 or abs(axis.dot(up)) > .001:
            raise ValueError("Armor cross-section must be perpendicular to its length: " + name)
        center_offset = up * offset
        a = a + center_offset
        b = b + center_offset
        # Beveled-looking chamfered rectangle: six corners per end.
        def ring(p, width):
            w, h = width, height
            return [
                p - side*w - up*h*.62,
                p + side*w - up*h*.62,
                p + side*w + up*h*.50,
                p + side*w*.45 + up*h,
                p - side*w*.45 + up*h,
                p - side*w + up*h*.50,
            ]
        va, vb = ring(a, width_a), ring(b, width_b)
        verts = va + vb
        faces = [tuple(reversed(range(6))), tuple(6+i for i in range(6))]
        for i in range(6):
            j = (i + 1) % 6
            faces.append((i, j, 6+j, 6+i))
        return self.mesh(name, verts, faces, key, bone)

    def tube(self, name, points, radius, key, bone, sides=12):
        points = [Vector(p) for p in points]
        verts, faces = [], []
        for i, p in enumerate(points):
            tangent = (points[min(i+1, len(points)-1)] - points[max(0, i-1)]).normalized()
            ref = Vector((0, 0, 1)) if abs(tangent.z) < .8 else Vector((0, 1, 0))
            side = tangent.cross(ref).normalized()
            up = tangent.cross(side).normalized()
            for j in range(sides):
                angle = math.tau * j / sides
                verts.append(p + radius * (side*math.cos(angle) + up*math.sin(angle)))
        for i in range(len(points)-1):
            for j in range(sides):
                k = i*sides+j
                n = i*sides+(j+1)%sides
                faces.append((k, n, n+sides, k+sides))
        faces.append(tuple(reversed(range(sides))))
        faces.append(tuple((len(points)-1)*sides+j for j in range(sides)))
        return self.mesh(name, verts, faces, key, bone)

    def cylinder(self, name, center, axis, radius, depth, key, bone, sides=16):
        axis = Vector(axis).normalized()
        ref = Vector((0, 0, 1)) if abs(axis.z) < .8 else Vector((0, 1, 0))
        side = axis.cross(ref).normalized()
        up = axis.cross(side).normalized()
        c = Vector(center)
        verts = []
        for end in (-.5, .5):
            p = c + axis * depth * end
            for j in range(sides):
                ang = math.tau*j/sides
                verts.append(p + radius*(side*math.cos(ang)+up*math.sin(ang)))
        faces = [tuple(reversed(range(sides))), tuple(sides+j for j in range(sides))]
        for j in range(sides):
            n=(j+1)%sides
            faces.append((j,n,sides+n,sides+j))
        return self.mesh(name, verts, faces, key, bone)


def bone_axis(rig, name):
    bone = rig.data.bones[name]
    a, b = bone.head_local.copy(), bone.tail_local.copy()
    axis = (b-a).normalized()
    side = bone.matrix_local.to_3x3() @ Vector((1,0,0))
    side = (side-axis*side.dot(axis)).normalized()
    if side.length < .001:
        side = axis.cross(Vector((0,0,1))).normalized()
    up = axis.cross(side).normalized()
    return a, b, axis, side, up


def _apply_armor():
    root = bpy.data.objects.get("LEAPER_ROOT")
    rig = bpy.data.objects.get("ARM_Leaper_Final")
    if not root or not rig or rig.type != "ARMATURE":
        raise RuntimeError("Open the existing Leaper scene with LEAPER_ROOT and ARM_Leaper_Final.")
    if bpy.context.mode != "OBJECT":
        raise RuntimeError("Switch to Object Mode before running the V25 pass.")
    required = {"body", "head", "rear_power"}
    for leg in LEGS:
        required.update({leg+"_upper", leg+"_lower", leg+"_foot"})
    missing = sorted(required - set(rig.data.bones.keys()))
    if missing:
        raise RuntimeError("Missing existing bones: " + ", ".join(missing))

    old = [o for o in bpy.context.scene.objects
           if belongs(o, rig, root) and o.get(OWNER) == VERSION]
    for obj in old:
        remove_owned(obj)
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        collection = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(collection)
    mats = {key: material(key) for key in PALETTE}
    builder = Builder(rig, collection, mats)
    saved_pose = rig.data.pose_position
    scene_frame = bpy.context.scene.frame_current
    rig.data.pose_position = "REST"
    bpy.context.view_layer.update()

    # Match the reference: thick segmented angular shells with recessed center strips.
    for leg in LEGS:
        for part, scale in (("upper", 1.0), ("lower", .90)):
            name = leg + "_" + part
            a, b, axis, side, up = bone_axis(rig, name)
            length = (b-a).length
            width = length * .16 * scale
            height = length * .17 * scale
            # Shell sits just above the existing armor envelope.
            builder.prism("V25_"+name+"_ArmorShell", a, b, side, up,
                          width, width*.86, height, "Armor", name, offset=height*.10)
            builder.prism("V25_"+name+"_EdgePlate", a+(b-a)*.10, a+(b-a)*.90,
                          side, up, width*.72, width*.55, height*.42,
                          "ArmorEdge", name, offset=height*.57)
            builder.tube("V25_"+name+"_InsetRail",
                         [a+(b-a)*.18+up*height*.64,
                          a+(b-a)*.82+up*height*.64],
                         max(.012, height*.075), "Inner", name, 8)
            # Orange/rust accent is a narrow service mark, not a glowing strip.
            builder.prism("V25_"+name+"_RustMark", a+(b-a)*.31, a+(b-a)*.40,
                          side, up, width*.76, width*.70, height*.10,
                          "RustAccent", name, offset=height*.82)

        # Heavy circular joint housings, attached to the upper bone so they seat on
        # the original joint objects and follow the existing animation.
        upper = leg + "_upper"
        lower = leg + "_lower"
        for label, p, bone_name, radius in (
            ("Hip", rig.data.bones[upper].head_local, upper, .14),
            ("Knee", rig.data.bones[upper].tail_local, upper, .125),
            ("Ankle", rig.data.bones[lower].tail_local, lower, .10),
        ):
            _, _, axis, side, up = bone_axis(rig, bone_name)
            builder.cylinder("V25_"+leg+"_"+label+"_Bearing", p, side,
                             radius, radius*.38, "Bearing", bone_name, 16)
            builder.cylinder("V25_"+leg+"_"+label+"_Inner", p+side*radius*.21, side,
                             radius*.57, radius*.12, "Inner", bone_name, 16)

    # Broad thorax armor plates around the existing body bone.
    body = rig.data.bones["body"]
    body_center = (body.head_local + body.tail_local) * .5
    builder.prism("V25_Thorax_TopArmor", body_center+Vector((-.34,0,.16)),
                  body_center+Vector((.30,0,.16)), Vector((0,1,0)), Vector((0,0,1)),
                  .42, .35, .18, "Armor", "body", offset=0)
    builder.prism("V25_Thorax_FrontArmor", body_center+Vector((.22,0,-.14)),
                  body_center+Vector((.56,0,-.14)), Vector((0,1,0)), Vector((0,0,1)),
                  .38, .28, .16, "ArmorEdge", "body", offset=0)
    for side_sign in (-1, 1):
        y = side_sign*.37
        builder.prism("V25_Thorax_SideArmor_"+str(side_sign),
                      body_center+Vector((-.28,y,0)), body_center+Vector((.32,y,0)),
                      Vector((0,1,0)), Vector((0,0,1)), .12, .10, .17,
                      "Armor", "body", offset=0)

    # Keep the existing alien face and all gameplay emitters. No independent
    # always-red reactor: red continues to mean attacking in the existing system.
    # Original object slots and existing material nodes are never rewritten.

    root["RobotArmorVersion"] = VERSION
    root["RobotArmorStyle"] = "Heavy angular combat shell; alien predator face retained"
    root["RobotArmorEmitter"] = "Existing state lights and weak points unchanged"
    rig.data.pose_position = saved_pose
    bpy.context.scene.frame_set(scene_frame)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    print("AFTERFALL LEAPER V25 ARMOR PASS COMPLETE")
    print("Added experimental angular armor shells and joint bearings.")
    print("Alien face, rig, weak points, actions and NLA were preserved.")
    print("Save As a NEW .blend after checking animation and clearances.")
    return builder.parts


def apply_armor():
    """Restore the artist's pose/frame/selection even if generation fails."""
    scene = bpy.context.scene
    frame, subframe = scene.frame_current, scene.frame_subframe
    selected = [obj.name for obj in bpy.context.selected_objects]
    active_obj = bpy.context.view_layer.objects.active
    active_name = active_obj.name if active_obj else None
    rig = bpy.data.objects.get("ARM_Leaper_Final")
    pose = rig.data.pose_position if rig and rig.type == "ARMATURE" else None
    try:
        return _apply_armor()
    finally:
        if pose is not None:
            rig.data.pose_position = pose
        scene.frame_set(frame, subframe=subframe)
        if bpy.context.mode == "OBJECT":
            bpy.ops.object.select_all(action="DESELECT")
            for name in selected:
                obj = bpy.data.objects.get(name)
                if obj:
                    obj.select_set(True)
            active = bpy.data.objects.get(active_name) if active_name else None
            if active:
                bpy.context.view_layer.objects.active = active
        bpy.context.view_layer.update()


if __name__ == "__main__":
    apply_armor()
