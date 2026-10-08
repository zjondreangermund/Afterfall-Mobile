#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Player/AFCharacter.h"
#include "Player/AFTraversalMontageFactory.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "AnimNotifyState_MotionWarping.h"
#include "RootMotionModifier_SkewWarp.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAFTraversalMontageTest, "Afterfall.Traversal.MontageGeneration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAFTraversalMontageTest::RunTest(const FString& Parameters)
{
    const AAFCharacter* Defaults = GetDefault<AAFCharacter>();
    const TSoftObjectPtr<UAnimSequenceBase> Sources[] = {
        Defaults->HurdleRunAnimation, Defaults->VaultRunAnimation, Defaults->VaultWalkAnimation,
        Defaults->MantleLowAnimation, Defaults->MantleMediumAnimation, Defaults->LedgeClimbAnimation,
        Defaults->LedgeCatchAnimation
    };
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Sources); ++Index)
    {
        UAnimSequence* Source = Cast<UAnimSequence>(Sources[Index].LoadSynchronous());
        if (!TestNotNull(*Sources[Index].ToString(), Source)) continue;
        const bool bRootBefore = Source->bEnableRootMotion;
        const bool bLockBefore = Source->bForceRootLock;
        const int32 NotifyCountBefore = Source->Notifies.Num();
        const bool bCatch = Index == 6;
        UAnimMontage* Montage = AFTraversalMontageFactory::Create(Source, GetTransientPackage(), bCatch, 0.92f);
        if (!TestNotNull(TEXT("Generated montage"), Montage)) continue;
        FString Error;
        const bool bValid = AFTraversalMontageFactory::Validate(Montage, Error);
        TestTrue(*FString::Printf(TEXT("Valid generated montage: %s"), *Error), bValid);
        TestTrue(TEXT("Root motion retained"), Montage->HasRootMotion());
        TestFalse(TEXT("No premature automatic blend out"), Montage->bEnableAutoBlendOut);
        TestEqual(TEXT("Source root motion setting unchanged"), bool(Source->bEnableRootMotion), bRootBefore);
        TestEqual(TEXT("Source root lock unchanged"), bool(Source->bForceRootLock), bLockBefore);
        TestEqual(TEXT("Source notifies unchanged"), Source->Notifies.Num(), NotifyCountBefore);
        TestTrue(TEXT("Catch trimmed at held pose; other clips retain full length"),
            FMath::IsNearlyEqual(Montage->GetPlayLength(), Source->GetPlayLength() * (bCatch ? 0.92f : 1.f)));
        // Reject a bad asset before it can switch the character to Flying.
        auto* Notify = Cast<UAnimNotifyState_MotionWarping>(Montage->Notifies[0].NotifyStateClass);
        auto* Warp = Notify ? Cast<URootMotionModifier_SkewWarp>(Notify->RootMotionModifier) : nullptr;
        if (!TestNotNull(TEXT("Skew warp config"), Warp)) continue;
        Warp->bIgnoreZAxis = true;
        TestFalse(TEXT("Invalid vertical warp rejected"), AFTraversalMontageFactory::Validate(Montage, Error));
        Warp->bIgnoreZAxis = false;
        Warp->WarpTargetName = TEXT("WrongTarget");
        TestFalse(TEXT("Mismatched target rejected"), AFTraversalMontageFactory::Validate(Montage, Error));
    }
    return !HasAnyErrors();
}
#endif
