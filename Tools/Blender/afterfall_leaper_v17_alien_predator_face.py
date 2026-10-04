"""Afterfall Leaper V1.7: an original alien-machine predator head.

Open Leaper_Standard_Final.blend, then run this file from Blender's Text Editor.
Requires the final rig and V1.3 weak-point bones. V1.6B-F are NOT prerequisites.
Builds in armature REST space; preserves the action, current frame and bone rest
transforms. Re-running replaces only this pass's meshes. Nothing is auto-saved.
"""

import math

ROOT_NAME = "LEAPER_ROOT"
RIG_NAME = "ARM_Leaper_Final"
VERSION = "1.7"
OWNER_KEY = "AfterfallFacePass"
COLLECTION_NAME = "LEAPER_V17_AlienFace"
FACE_BONES = {"head", "weak_eye", "cover_eye"}
LEGACY_PASSES = ("V16B_", "V16C_", "V16D_", "V16E_", "V16F_")
LEGACY_NAMES = {
    "Eye_Lens", "Eye_OuterRing", "Eye_InnerRing", "WP_Eye_Cover",
    "V16_SensorSlit", "Sensor_Head", "Sensor_Main", "Sensor_Main_Ring",
    "V06_SensorChin", "V06_CheekGuard_L", "V06_CheekGuard_R",
}

# Existing gameplay slot names are deliberately unchanged.
MATERIALS = {
    "shell": ("LEAP_V17_Obsidian", (0.018, 0.023, 0.030), 0.78, 0.31, 0.0),
    "edge": ("LEAP_V17_CarapaceEdge", (0.065, 0.079, 0.095), 0.82, 0.29, 0.0),
    "mech": ("LEAP_V17_InnerMechanism", (0.009, 0.012, 0.017), 0.67, 0.38, 0.0),
    "eye": ("LEAP_WP_Eye_Grey", (0.095, 0.102, 0.110), 0.80, 0.31, 0.0),
    "scan": ("LEAP_SIGNAL_Scan_White", (1.0, 0.92, 0.72), 0.04, 0.18, 5.0),
    "alert": ("LEAP_SIGNAL_Alert_Yellow", (1.0, 0.44, 0.01), 0.04, 0.18, 7.0),
    "attack": ("LEAP_SIGNAL_Attack_Red", (1.0, 0.025, 0.012), 0.04, 0.18, 9.0),
    "discovered": ("LEAP_WP_Discovered_PaleYellow", (1.0, 0.84, 0.46), 0.12, 0.21, 4.0),
    "hit": ("LEAP_WP_Hit_WhiteYellow", (1.0, 0.95, 0.60), 0.06, 0.16, 10.0),
}


def loft(sections, sides=8):
    """Closed faceted shell; sections are (forward, side, up, halfwidth, height)."""
    verts = []
    for x, y, z, width, height in sections:
        for j in range(sides):
            a = math.tau * j / sides
            verts.append((x, y + width * math.cos(a), z + height * math.sin(a)))
    faces = [tuple(reversed(range(sides)))]
    for i in range(len(sections) - 1):
        for j in range(sides):
            k = (j + 1) % sides
            faces.append((i*sides+j, i*sides+k, (i+1)*sides+k, (i+1)*sides+j))
    faces.append(tuple(range((len(sections)-1)*sides, len(verts))))
    return verts, faces


def plate(outline, depth=0.12, ridge=0.06):
    """Convex contour with varying depth and a raised triangular-fan front."""
    n = len(outline)
    verts = list(outline) + [(x-depth, y*0.96, z) for x, y, z in outline]
    center = tuple(sum(p[k] for p in outline) / n for k in range(3))
    verts.append((center[0]+ridge, center[1], center[2]))
    faces = [tuple(reversed(range(n, n*2)))]
    for i in range(n):
        j = (i+1) % n
        faces.extend(((i, j, 2*n), (i, n+i, n+j, j)))
    return verts, faces


def merge_meshes(meshes):
    verts, faces = [], []
    for vv, ff in meshes:
        offset = len(verts)
        verts.extend(vv)
        faces.extend(tuple(i+offset for i in f) for f in ff)
    return verts, faces


def signal_arc(start, end, segments):
    """Capped tube: the circular sensor stays distinct from the outer skull."""
    verts, faces = [], []
    sides, radius, tube = 6, 0.54, 0.031
    for i in range(segments+1):
        a = math.radians(start + (end-start)*i/segments)
        for j in range(sides):
            b = math.tau*j/sides
            r = radius + tube*math.cos(b)
            verts.append((-0.16+tube*math.sin(b), r*math.cos(a), r*math.sin(a)))
    faces.append(tuple(reversed(range(sides))))
    for i in range(segments):
        for j in range(sides):
            k = (j+1) % sides
            faces.append((i*sides+j, i*sides+k, (i+1)*sides+k, (i+1)*sides+j))
    faces.append(tuple(range(segments*sides, (segments+1)*sides)))
    return verts, faces


def face_geometry():
    """Mesh recipes in eye-radius units, +X forward, +Y sideways, +Z up.

    Kept independent of bpy so geometry can also be inspected outside Blender.
    All broad plates have varying depth; mandibles are tapered swept volumes.
    """
    specs = []

    def add(name, mesh, material="shell", bone="head"):
        specs.append({"name": "V17_"+name, "mesh": mesh, "material": material, "bone": bone})

    add("CranialCarapace", loft([
        (-2.35, 0, 0.43, 0.28, 0.22),
        (-1.70, 0, 0.76, 0.78, 0.43),
        (-0.90, 0, 0.90, 1.08, 0.42),
        (-0.20, 0, 0.83, 0.91, 0.30),
        (0.24, 0, 0.64, 0.43, 0.15),
    ]))
    add("CrownKeel", loft([
        (-2.34, 0, 0.64, 0.045, 0.035),
        (-1.65, 0, 1.16, 0.11, 0.12),
        (-0.87, 0, 1.30, 0.14, 0.09),
        (-0.14, 0, 1.05, 0.08, 0.035),
        (0.32, 0, 0.61, 0.025, 0.025),
    ], 4), "edge")
    add("NasalKeel", plate([
        (0.25,-0.12,0.70), (0.25,0.12,0.70), (0.61,0.09,0.29),
        (0.64,0,0.17), (0.61,-0.09,0.29),
    ], 0.10, 0.045))

    for sign, label in ((-1, "L"), (1, "R")):
        def mirror(points):
            return [(x, sign*y, z) for x, y, z in points]

        add("Brow_"+label, plate(mirror([
            (-0.50, 0.54, 1.03), (-0.58, 1.18, 0.76),
            (-0.02, 1.31, 0.53), (0.47, 0.64, 0.22),
            (0.58, 0.08, 0.26),
        ]), 0.15, 0.12))
        add("BrowEdge_"+label, merge_meshes([
            plate(mirror([(0.005,1.30,0.52), (0.49,0.64,0.21),
                          (0.46,0.64,0.28), (-0.04,1.26,0.58)]), 0.035, 0.015),
            plate(mirror([(0.49,0.64,0.21), (0.60,0.08,0.25),
                          (0.54,0.12,0.31), (0.46,0.64,0.28)]), 0.035, 0.015),
        ]), "edge")
        add("Temple_"+label, plate(mirror([
            (-1.13, 0.88, 0.67), (-0.42, 1.26, 0.45),
            (-0.13, 1.09, -0.35), (-0.63, 0.83, -0.69),
            (-1.40, 0.66, -0.14),
        ]), 0.18, 0.12))

        # Four hooked mouthparts form the alien silhouette; every part of the
        # detachable jaw uses cover_eye and the SAME dormant material slot.
        upper = [(-0.58, 1.06, 0.08, 0.22, 0.25),
                 (-0.05, 1.27, -0.18, 0.20, 0.20),
                 (0.38, 1.05, -0.51, 0.13, 0.13),
                 (0.68, 0.61, -0.32, 0.018, 0.025)]
        lower = [(-0.76, 0.81, -0.42, 0.20, 0.26),
                 (-0.27, 1.03, -0.89, 0.21, 0.23),
                 (0.26, 0.76, -1.22, 0.15, 0.13),
                 (0.67, 0.30, -0.81, 0.015, 0.022)]
        for name, sections in (("UpperMandible_", upper), ("LowerMandible_", lower)):
            add(name+label, loft([(x, sign*y, z, w, h) for x,y,z,w,h in sections], 6),
                "eye", "cover_eye")

        # Layered gills join the temple to the rear skull, following its taper.
        for i in range(3):
            x = -1.24 + 0.28*i
            y = 0.75 + 0.12*i
            add("Gill_"+label+str(i+1), plate(mirror([
                (x, y, 0.46), (x+0.11, y+0.11, 0.41),
                (x+0.22, y+0.07, -0.31), (x+0.08, y-0.04, -0.20),
            ]), 0.05, 0.025), "edge")

    add("InnerJaw", plate([
        (-0.36, -0.60, -0.38), (-0.36, 0.60, -0.38),
        (-0.13, 0.39, -0.91), (0.05, 0, -1.17), (-0.13, -0.39, -0.91),
    ], 0.22, 0.08), "mech")
    add("WP_Eye_Keel", plate([
        (0.12, -0.29, -0.59), (0.12, 0.29, -0.59),
        (0.37, 0.20, -0.91), (0.46, 0, -1.14), (0.37, -0.20, -0.91),
    ], 0.095, 0.04), "eye", "cover_eye")
    add("SensorSocket", loft([(-0.43,0,0,0.53,0.53), (-0.24,0,0,0.51,0.51)], 24), "mech")
    add("SensorLens", loft([(-0.23,0,0,0.29,0.29), (-0.185,0,0,0.27,0.27)], 24), "shell")
    add("SensorIris", loft([(-0.18,0,0,0.12,0.12), (-0.16,0,0,0.11,0.11)], 12), "mech")
    signal = [signal_arc(a,b,n) for a,b,n in ((23,157,12), (171,243,7),
                                             (257,283,4), (297,369,7))]
    add("StateLight", merge_meshes(signal), "scan")

    # These tiny, fully enclosed tetrahedra survive selected-mesh FBX export.
    # Hidden carriers used by older passes disappeared from visible-only exports.
    for i, key in enumerate(("alert", "attack", "discovered", "hit")):
        x, z, d = -1.30+0.07*i, 0.90, 0.012
        add("MaterialBank_"+key, ([(x,0,z), (x+d,0,z), (x,d,z), (x,0,z+d)],
                                 [(0,2,1), (0,1,3), (1,2,3), (2,0,3)]), key)
    return specs


def apply_face():
    import bpy
    import bmesh
    from mathutils import Matrix, Vector

    root = bpy.data.objects.get(ROOT_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if not root or not rig or rig.type != 'ARMATURE':
        raise RuntimeError("Open Leaper_Standard_Final.blend with LEAPER_ROOT and ARM_Leaper_Final first.")
    missing = FACE_BONES - set(rig.data.bones.keys())
    if missing:
        raise RuntimeError("Run the V1.3 weak-point pass first. Missing bones: "+", ".join(sorted(missing)))
    if bpy.context.mode != 'OBJECT':
        raise RuntimeError("Switch to Object Mode before running the V1.7 face pass.")

    def belongs(o):
        parent = o.parent
        while parent:
            if parent in (root, rig):
                return True
            parent = parent.parent
        return any(m.type == 'ARMATURE' and m.object == rig for m in o.modifiers)

    def face_bound(o):
        if o.parent == rig and o.parent_type == 'BONE':
            return o.parent_bone in FACE_BONES
        if o.type != 'MESH' or not o.data.vertices:
            return False
        if not any(m.type == 'ARMATURE' and m.object == rig for m in o.modifiers):
            return False
        deform_groups = {g.index: g.name for g in o.vertex_groups
                         if g.name in rig.data.bones and rig.data.bones[g.name].use_deform}
        for v in o.data.vertices:
            weights = [g for g in v.groups if g.weight > 0.0001 and g.group in deform_groups]
            if not weights or any(deform_groups[g.group] not in FACE_BONES for g in weights):
                return False  # Never retire a joined body/leg mesh.
        return True

    def legacy_name(name):
        name = name.rsplit('.', 1)[0] if name.rsplit('.', 1)[-1].isdigit() else name
        return (name in LEGACY_NAMES or name.startswith(LEGACY_PASSES)
                or name.startswith(("Head_", "Eye_", "Brow_", "Mandible", "Sensor_Aux_")))

    def mixed_body_mesh(o):
        if o.type != 'MESH':
            return False
        deform_groups = {g.index: g.name for g in o.vertex_groups
                         if g.name in rig.data.bones and rig.data.bones[g.name].use_deform}
        used = {deform_groups[g.group] for v in o.data.vertices for g in v.groups
                if g.weight > 0.0001 and g.group in deform_groups}
        return bool(used & FACE_BONES) and bool(used - FACE_BONES)

    old_generated = [o for o in bpy.data.objects if o.get(OWNER_KEY) == VERSION and belongs(o)]
    old_face = [o for o in bpy.data.objects if o.type in {'MESH', 'CURVE'} and belongs(o)
                and o not in old_generated and not mixed_body_mesh(o)
                and (legacy_name(o.name) or face_bound(o))]
    saved_pose = rig.data.pose_position
    created = []
    try:
        # A crouched/action frame is NOT the bind pose. Building in pose space
        # and then adding an Armature modifier would apply the pose a second time.
        rig.data.pose_position = 'REST'
        bpy.context.view_layer.update()
        rig_inverse = rig.matrix_world.inverted()
        eye = bpy.data.objects.get("Eye_Lens")
        if eye and eye.type == 'MESH' and belongs(eye):
            transform = rig_inverse @ eye.matrix_world
            points = [transform @ Vector(v) for v in eye.bound_box]
            anchor = sum(points, Vector()) / len(points)
        else:
            anchor = rig.data.bones["weak_eye"].head_local.copy()
            points = []
        body = bpy.data.objects.get("Core_Body")
        body_pos = (rig_inverse @ body.matrix_world.translation if body and belongs(body)
                    else rig.data.bones["head"].head_local.copy())
        forward = anchor-body_pos
        # The final Leaper faces +X. Use its local up, never global world Z.
        forward.z = 0.0
        if forward.length < 0.0001:
            forward = Vector((1,0,0))
        forward.normalize()
        up = Vector((0,0,1))
        side = up.cross(forward).normalized()
        radius = float(root.get("V17_FaceRadius", 0.0))
        if radius <= 0:
            diameter = max((max(p.dot(axis) for p in points)-min(p.dot(axis) for p in points)
                            for axis in (side, up)), default=0.48)
            radius = max(0.23, diameter*0.53)

        collection = bpy.data.collections.get(COLLECTION_NAME)
        if collection is None:
            collection = bpy.data.collections.new(COLLECTION_NAME)
            bpy.context.scene.collection.children.link(collection)
        elif collection not in list(bpy.context.scene.collection.children):
            # It may already be nested inside a user collection in this scene.
            if collection not in list(bpy.context.scene.collection.children_recursive):
                bpy.context.scene.collection.children.link(collection)
        collection.hide_viewport = False
        collection.hide_render = False

        materials = {}
        for key, (name, color, metal, rough, strength) in MATERIALS.items():
            material = bpy.data.materials.get(name)
            if material is None:
                material = bpy.data.materials.new(name)
                material.use_nodes = True
                shader = material.node_tree.nodes.get("Principled BSDF")
                shader.inputs["Base Color"].default_value = (*color,1)
                shader.inputs["Metallic"].default_value = metal
                shader.inputs["Roughness"].default_value = rough
                shader.inputs["Emission Color"].default_value = (*color,1)
                shader.inputs["Emission Strength"].default_value = strength
                material.diffuse_color = (*color,1)
            materials[key] = material

        specs = face_geometry()
        # Connect the elongated cranium to the original head attachment.
        back = min(-1.8, (body_pos-anchor).dot(forward)/radius)
        specs.append({"name":"V17_NeckBridge", "mesh":loft([
            (back,0,0.35,0.31,0.25), (-1.35,0,0.45,0.48,0.33),
        ], 8), "material":"mech", "bone":"head"})
        for spec in specs:
            vv, ff = spec["mesh"]
            mesh = bpy.data.meshes.new(spec["name"]+"_Mesh")
            mesh.from_pydata([anchor+radius*(forward*x+side*y+up*z) for x,y,z in vv], [], ff)
            mesh.update()
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            bm.to_mesh(mesh)
            bm.free()
            o = bpy.data.objects.new(spec["name"], mesh)
            created.append((o, spec["name"]))
            collection.objects.link(o)
            o[OWNER_KEY] = VERSION
            mesh.materials.append(materials[spec["material"]])
            o.color = materials[spec["material"]].diffuse_color
            o.parent = rig
            o.matrix_parent_inverse = Matrix.Identity(4)
            o.matrix_basis = Matrix.Identity(4)
            group = o.vertex_groups.new(name=spec["bone"])
            group.add(list(range(len(mesh.vertices))), 1.0, 'REPLACE')
            arm = o.modifiers.new("Leaper_Final_Rig", 'ARMATURE')
            arm.object = rig
            arm.use_deform_preserve_volume = False

        # Commit only after the full replacement has been built successfully.
        for o in old_face:
            if "V17_PreviousVisibility" not in o:
                o["V17_PreviousVisibility"] = [o.hide_viewport, o.hide_render, o.hide_get(), o.hide_select]
            o.hide_set(True)
            o.hide_render = True
            o.hide_viewport = True
            o.hide_select = True
            o["V17_SupersededFace"] = True
        for o in old_generated:
            data = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if data.users == 0:
                bpy.data.meshes.remove(data)
        for o, name in created:
            o.name = name
            o.data.name = name+"_Mesh"
        root["V17_FaceRadius"] = radius
        root["FaceRefitVersion"] = VERSION
        root["FaceDesign"] = "Elongated carapace, swept brows, four hooked mandibles, recessed circular sensor."
        root["EyeWeakPoint"] = "V17 mandibles and eye keel: cover_eye / LEAP_WP_Eye_Grey."
        root["SignalStateRule"] = "Scanning white; Alert yellow; Attacking red."
        root["FaceCircleRule"] = "The sensor is circular; the skull and jaw have an angular alien silhouette."
    except Exception:
        for o, _ in created:
            data = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if data.users == 0:
                bpy.data.meshes.remove(data)
        raise
    finally:
        rig.data.pose_position = saved_pose
        bpy.context.view_layer.update()

    print("AFTERFALL Leaper V1.7 alien predator face applied.")
    print("Retired original/previous face parts:", ", ".join(o.name for o in old_face))
    print("Rig, actions, frame and non-face parts preserved. Save As, then re-export the visible Leaper meshes.")
    return [o for o, _ in created]


if __name__ == "__main__":
    apply_face()
