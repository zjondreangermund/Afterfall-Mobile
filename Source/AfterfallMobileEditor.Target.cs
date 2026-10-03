using UnrealBuildTool;
using System.Collections.Generic;

public class AfterfallMobileEditorTarget : TargetRules
{
    public AfterfallMobileEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("AfterfallMobile");
    }
}
