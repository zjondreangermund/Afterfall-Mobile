# Afterfall: compact rocky canyon test world

This is a **lightweight, editor-only prototype** inspired by the rocky terrain feel of Valley of the Ancient. It does not download, copy or depend on that large sample.

## Run in Unreal Engine 5.8

1. **Back up your local project**, then synchronize your Git checkout with `main`. If Unreal is open, close it before updating project files.
2. Open **AfterfallMobile.uproject**. Your project was found locally at `D:\\New folder\\Afterfallmobile\\Afterfallmobile.uproject` in the PowerShell output; a second backup copy also exists.
3. Make a **new empty level** in Unreal Editor, not your existing traversal or player level. Do not replace your current map.
4. Enable **Python Editor Script Plugin** if needed (the repository already enables it in the `.uproject`).
5. Use **Tools → Execute Python Script**, then select `Content/Python/af_build_rocky_test.py`.
6. Press **F** with an actor selected to frame the generated area, then **File → Save Current Level As** `/Game/Afterfall/Maps/L_Rocky_Test`.
7. Add your existing `AFTraversalTestCourse`, player character and Leaper to this level once the scene runs correctly. Create/bake NavMesh for the chase test and verify spawn/ground collision.

### Output
- 250m × 250m flat ground with two boulder ridge banks and a central movement corridor
- Around 78 boulder placeholders using built-in sphere meshes, five obstacle platforms and one PlayerStart (if none exists)
- Deterministic layout; no external assets, downloaded worlds or third-party plugins
- No modifications to game mode, existing Blueprints, player code, Leaper behaviour or HOUND

### Important limits
This is a **blockout**, not a sculpted landscape. The default engine spheres look rounded and do not have genuine rock silhouettes or rocky textures. We will replace them with inexpensive mobile-ready rocks or a small licensed asset pack after validating the gameplay. The script creates many individual StaticMeshActors for convenient editing, so optimize repeated geometry using instancing after the layout is approved.

Run only in an empty test level. The script refuses to create duplicate prefixed actors, but it does not remove existing content. If an execution fails halfway, use Unreal Undo or a fresh empty level.

### GPU settings
On a GTX 780 (3 GB), use Low scalability, avoid Nanite/Lumen/VSM and large textures, and test the level in editor before building Android.
