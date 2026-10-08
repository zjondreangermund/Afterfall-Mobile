#include "Player/AFTraversalMontageFactory.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "AnimNotifyState_MotionWarping.h"
#include "RootMotionModifier_SkewWarp.h"
#if WITH_EDITOR
#include "AssetRegistry/AssetRegistryModule.h"
#include "Misc/PackageName.h"
#include "UObject/SavePackage.h"
#endif

namespace AFTraversalMontageFactory
{
UAnimMontage* Create(UAnimSequence* Source, UObject* Outer, bool bCatch, float CatchFraction)
{
    if (!Source || !Source->GetSkeleton() || Source->GetPlayLength() <= KINDA_SMALL_NUMBER)
    {
        return nullptr;
    }
    // Never change the imported source: jumps and other characters may share it.
    UAnimSequence* Playback = DuplicateObject<UAnimSequence>(Source, Outer,
        MakeUniqueObjectName(Outer, Source->GetClass(), FName(*FString::Printf(TEXT("AFTraversal_%s"), *Source->GetName()))));
    Playback->ClearFlags(RF_Public | RF_Standalone);
    Playback->SetFlags(RF_Transient);
    Playback->bEnableRootMotion = true;
    Playback->bForceRootLock = true;
    Playback->RootMotionRootLock = ERootMotionRootLock::AnimFirstFrame;
    Playback->Notifies.RemoveAll([](const FAnimNotifyEvent& Event)
    {
        return Event.NotifyStateClass && Event.NotifyStateClass->IsA<UAnimNotifyState_MotionWarping>();
    });

    UAnimMontage* Montage = UAnimMontage::CreateSlotAnimationAsDynamicMontage(
        Playback, SlotName, 0.10f, 0.12f, 1.f, 1, -1.f, 0.f);
    if (!Montage)
    {
        return nullptr;
    }
    Montage->Rename(nullptr, Outer);
    // Do not blend out early and lose root translation before the target is reached.
    // The character ends completed traversals with an explicit short blend-out.
    Montage->bEnableAutoBlendOut = false;
    const float Length = Source->GetPlayLength() *
        (bCatch ? FMath::Clamp(CatchFraction, 0.1f, 0.98f) : 1.f);
    Montage->SlotAnimTracks[0].AnimTrack.AnimSegments[0].AnimEndTime = Length;
    Montage->SetCompositeLength(Length);

    UAnimNotifyState_MotionWarping* Notify = NewObject<UAnimNotifyState_MotionWarping>(Montage);
    URootMotionModifier_SkewWarp* Warp = NewObject<URootMotionModifier_SkewWarp>(Notify);
    Warp->WarpTargetName = TargetName;
    Warp->bWarpTranslation = true;
    Warp->bIgnoreZAxis = false;
    Warp->bWarpRotation = true;
    Warp->bWarpToFeetLocation = true;
    Warp->WarpPointAnimProvider = EWarpPointAnimProvider::None;
    Warp->RotationType = EMotionWarpRotationType::Default;
    Notify->RootMotionModifier = Warp;

    FAnimNotifyEvent Event;
    Event.NotifyName = TEXT("Motion Warping");
    Event.NotifyStateClass = Notify;
    Event.Link(Montage, 0.f);
    Event.SetDuration(Length);
    Event.EndLink.Link(Montage, Length);
    Montage->Notifies.Add(Event);
#if WITH_EDITORONLY_DATA
    if (Montage->AnimNotifyTracks.IsEmpty())
    {
        Montage->AnimNotifyTracks.Add(FAnimNotifyTrack(TEXT("Traversal"), FLinearColor::Green));
    }
#endif
#if WITH_EDITOR
    Montage->RefreshCacheData();
#endif
    return Montage;
}

bool Validate(const UAnimMontage* Montage, FString& OutError)
{
    if (!Montage || Montage->GetPlayLength() <= KINDA_SMALL_NUMBER ||
        Montage->SlotAnimTracks.Num() != 1 || Montage->SlotAnimTracks[0].SlotName != SlotName ||
        Montage->SlotAnimTracks[0].AnimTrack.AnimSegments.IsEmpty())
    {
        OutError = TEXT("Traversal montage must have one TraversalSlot track and a positive duration.");
        return false;
    }
    for (const FAnimSegment& Segment : Montage->SlotAnimTracks[0].AnimTrack.AnimSegments)
    {
        const UAnimSequence* Sequence = Cast<UAnimSequence>(Segment.GetAnimReference());
        if (!Sequence || !Sequence->bEnableRootMotion)
        {
            OutError = TEXT("Every traversal segment must be a root-motion-enabled Animation Sequence.");
            return false;
        }
        // A second nested window could apply two conflicting root motion modifiers.
        for (const FAnimNotifyEvent& Event : Sequence->Notifies)
        {
            if (Cast<UAnimNotifyState_MotionWarping>(Event.NotifyStateClass))
            {
                OutError = TEXT("Put traversal warp windows on the montage, not also on its source sequence.");
                return false;
            }
        }
    }
    int32 WarpWindows = 0;
    for (const FAnimNotifyEvent& Event : Montage->Notifies)
    {
        const auto* Notify = Cast<UAnimNotifyState_MotionWarping>(Event.NotifyStateClass);
        if (!Notify) continue;
        const auto* Warp = Cast<URootMotionModifier_SkewWarp>(Notify->RootMotionModifier);
        if (!Warp || Warp->WarpTargetName != TargetName || !Warp->bWarpTranslation ||
            Warp->bIgnoreZAxis || !Warp->bWarpRotation || !Warp->bWarpToFeetLocation ||
            Warp->WarpPointAnimProvider != EWarpPointAnimProvider::None ||
            Event.GetDuration() <= KINDA_SMALL_NUMBER)
        {
            OutError = TEXT("Use Skew Warp, TraversalTarget, translation/rotation/feet on, Ignore Z off, provider None.");
            return false;
        }
        if (Event.GetEndTriggerTime() < Montage->GetPlayLength() - 0.05f && !Warp->bSubtractRemainingRootMotion)
        {
            OutError = TEXT("Endpoint warp window ends early: extend it to montage end or enable Subtract Remaining Root Motion.");
            return false;
        }
        ++WarpWindows;
    }
    if (WarpWindows != 1)
    {
        OutError = TEXT("Expected one endpoint warp window. Multiple contact windows need a different target contract.");
        return false;
    }
    return true;
}

#if WITH_EDITOR
UAnimMontage* SaveDefault(UAnimSequence* Source, const FString& AssetName, bool bCatch, float CatchFraction)
{
    const FString PackageName = TEXT("/Game/Afterfall/Animations/Traversal_Generated/") + AssetName;
    if (UAnimMontage* Existing = LoadObject<UAnimMontage>(nullptr, *(PackageName + TEXT(".") + AssetName)))
    {
        return Existing; // Keep authored timing and user edits on repeated runs.
    }
    if (FPackageName::DoesPackageExist(PackageName))
    {
        UE_LOG(LogTemp, Error, TEXT("Traversal setup: asset already exists with another type: %s"), *PackageName);
        return nullptr;
    }
    UPackage* Package = CreatePackage(*PackageName);
    UAnimMontage* Montage = Create(Source, Package, bCatch, CatchFraction);
    if (!Montage) return nullptr;
    Montage->Rename(*AssetName, Package);
    Montage->ClearFlags(RF_Transient);
    Montage->SetFlags(RF_Public | RF_Standalone);
    // The copied sequence is saved in the same package as a private subobject.
    UAnimSequence* Playback = Cast<UAnimSequence>(Montage->SlotAnimTracks[0].AnimTrack.AnimSegments[0].GetAnimReference());
    Playback->ClearFlags(RF_Transient);
    Montage->MarkPackageDirty();
    FAssetRegistryModule::AssetCreated(Montage);
    FSavePackageArgs Args;
    Args.TopLevelFlags = RF_Public | RF_Standalone;
    Args.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(PackageName, FPackageName::GetAssetPackageExtension());
    if (!UPackage::SavePackage(Package, Montage, *Filename, Args))
    {
        UE_LOG(LogTemp, Error, TEXT("Traversal setup: failed to save %s"), *Filename);
        return nullptr;
    }
    return Montage;
}
#endif
}
