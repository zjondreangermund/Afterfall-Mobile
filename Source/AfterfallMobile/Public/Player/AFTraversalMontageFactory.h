#pragma once

#include "CoreMinimal.h"

class UAnimMontage;
class UAnimSequence;

// Shared by runtime defaults and the editor's non-destructive asset generator.
namespace AFTraversalMontageFactory
{
    inline const FName TargetName(TEXT("TraversalTarget"));
    inline const FName SlotName(TEXT("TraversalSlot"));

    UAnimMontage* Create(UAnimSequence* Source, UObject* Outer, bool bCatch, float CatchFraction);
    bool Validate(const UAnimMontage* Montage, FString& OutError);
#if WITH_EDITOR
    UAnimMontage* SaveDefault(UAnimSequence* Source, const FString& AssetName, bool bCatch,
        float CatchFraction);
#endif
}
