"""Unreal Editor: Tools > Execute Python Script > select this file. Safe to rerun."""
import unreal


def setup():
    # Discover the existing player; do not create/replace a Blueprint or its AnimGraph.
    assets = unreal.EditorAssetLibrary.list_assets("/Game/Afterfall", recursive=True, include_folder=False)
    matches = [path for path in assets if path.rsplit("/", 1)[-1].split(".")[0] == "BP_AFCharacter"]
    if len(matches) != 1:
        raise RuntimeError("Expected one BP_AFCharacter under /Game/Afterfall; found: " + str(matches))
    blueprint = unreal.load_asset(matches[0])
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    defaults = unreal.get_default_object(blueprint.generated_class())
    if not hasattr(defaults, "generate_traversal_montages"):
        raise RuntimeError("Build the updated AfterfallMobileEditor target and restart Unreal first.")
    with unreal.ScopedEditorTransaction("Afterfall: generate traversal montage defaults"):
        blueprint.modify()
        defaults.modify()
        defaults.generate_traversal_montages()
        if not unreal.EditorAssetLibrary.save_loaded_asset(blueprint, only_if_is_dirty=False):
            raise RuntimeError("Could not save BP_AFCharacter. Check file permissions/source control.")
    if len(defaults.get_editor_property("traversal_montages")) != 8:
        raise RuntimeError("Some traversal clips are missing. See Output Log; existing assignments were saved.")
    unreal.log("Afterfall traversal setup finished. Existing montage overrides and AnimGraph preserved.")
    unreal.log("Keep the final TraversalSlot before Output Pose in ABP_Afterfall_Rifle. Play and use af.Traversal.Debug 1.")


setup()
