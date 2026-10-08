"""Architecture regressions; these do not compile UE or simulate CharacterMovement."""
from pathlib import Path
import ast
import json
import re

root = Path(__file__).resolve().parents[1]
source = (root / "Source/AfterfallMobile/Private/Player/AFCharacter.cpp").read_text()
factory = (root / "Source/AfterfallMobile/Private/Player/AFTraversalMontageFactory.cpp").read_text()
functions = dict(re.findall(r"(?:void|bool|float|FVector|TSoftObjectPtr<UAnimSequenceBase>) AAFCharacter::(\w+)\([^)]*\)(?: const)?\s*\{(.*?)(?=\n(?:void|bool|float|FVector|TSoftObjectPtr<UAnimSequenceBase>) AAFCharacter::|\Z)", source, re.S))
assert functions, "Parser must find character functions"
for name, body in functions.items():
    if re.search(r"\bSetActor(?:Location|Transform|Rotation)", body):
        assert name == "UpdateHanging", f"Manual movement returned in {name}"
    if "PlayFullBodySequence(" in body:
        assert name == "SetJumpVisualPhase", f"Single-node sequence playback leaked into {name}"
    if "IgnoreRootMotion" in body:
        assert name == "PlayFullBodySequence", f"Traversal discards root motion in {name}"
for name in ("StartTraversalMove", "EnterLedgeHang", "PlayTraversalMontage", "UpdateTraversal", "ClimbFromLedge"):
    assert "LoadSynchronous" not in functions[name], f"Asset load at interaction time in {name}"
assert "SetRootMotionMode(ERootMotionMode::RootMotionFromMontagesOnly)" in functions["PlayTraversalMontage"]
assert "IsTraversalPathClear()" in functions["StartTraversalMove"]
assert "FMath::Max3<double>" in functions["StartTraversalMove"]
assert "HasTraversalSupport" in functions["StartTraversalMove"]
assert "HasTraversalSupport" in functions["UpdateTraversal"]
assert "RemoveWarpTarget" in functions["EndTraversalMove"]
assert "DisableAllRootMotionModifiers" in functions["EndTraversalMove"]
assert "MOVE_Falling" in functions["EndTraversalMove"]
assert "bCompleted ? 0.12f : 0.f" in functions["EndTraversalMove"], "Abort must not keep moving during blend-out"
assert 'TEXT("FrontLedge")' not in source + factory
assert '"MotionWarping"' in (root / "Source/AfterfallMobile/AfterfallMobile.Build.cs").read_text()
project = json.loads((root / "AfterfallMobile.uproject").read_text())
assert any(p["Name"] == "MotionWarping" and p["Enabled"] for p in project["Plugins"])
ast.parse((root / "Content/Python/af_setup_traversal.py").read_text())
print("Traversal architecture checks passed (engine compilation/PIE still required)")
