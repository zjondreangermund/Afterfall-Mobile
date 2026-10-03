using UnrealBuildTool;
using System.Collections.Generic;

public class AfterfallMobileTarget : TargetRules
{
    public AfterfallMobileTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("AfterfallMobile");
    }
}
