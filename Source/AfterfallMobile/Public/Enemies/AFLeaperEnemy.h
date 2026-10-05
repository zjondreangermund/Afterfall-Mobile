#pragma once

#include "CoreMinimal.h"
#include "TimerManager.h"
#include "Enemies/AFEnemyBase.h"
#include "AFLeaperEnemy.generated.h"

class AAFLootPickup;
class UMaterialInterface;
class UAnimationAsset;
class USphereComponent;

UENUM(BlueprintType)
enum class EAFLeaperAlertState : uint8
{
    Scanning UMETA(DisplayName="Scanning"),
    Alert UMETA(DisplayName="Alert"),
    Attacking UMETA(DisplayName="Attacking")
};

UENUM(BlueprintType)
enum class EAFLeaperTraversalMode : uint8
{
    Ground UMETA(DisplayName="Ground"),
    SurfaceCrawl UMETA(DisplayName="Surface Crawl")
};

USTRUCT(BlueprintType)
struct FAFLeaperWeakPointDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    FName Id = NAME_None;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    FName HitBone = NAME_None;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    FName CoverBone = NAME_None;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    FName MaterialSlot = NAME_None;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points", meta=(ClampMin="1.0"))
    float MaxHealth = 30.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points", meta=(ClampMin="1.0"))
    float DamageMultiplier = 2.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    FName LootItemId = TEXT("LeaperArmorPlate");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points", meta=(ClampMin="1"))
    int32 LootQuantity = 1;
};

USTRUCT(BlueprintType)
struct FAFLeaperWeakPointState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    float CurrentHealth = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    float MaxHealth = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    bool bDiscovered = false;

    UPROPERTY(BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    bool bBroken = false;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
    FAFOnLeaperWeakPointDiscovered,
    FName,
    WeakPointId);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(
    FAFOnLeaperWeakPointHit,
    FName,
    WeakPointId,
    float,
    NormalizedHealth);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(
    FAFOnLeaperWeakPointBroken,
    FName,
    WeakPointId,
    FVector,
    WorldLocation);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
    FAFOnLeaperAlertStateChanged,
    EAFLeaperAlertState,
    NewState);

UCLASS()
class AFTERFALLMOBILE_API AAFLeaperEnemy : public AAFEnemyBase
{
    GENERATED_BODY()

public:
    AAFLeaperEnemy();

    virtual void Tick(float DeltaSeconds) override;

    virtual float TakeDamage(
        float DamageAmount,
        struct FDamageEvent const& DamageEvent,
        class AController* EventInstigator,
        AActor* DamageCauser) override;

    UFUNCTION(BlueprintCallable, Category="Afterfall|Leaper")
    bool TryPounceAt(AActor* TargetActor);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Leaper|Alert")
    void SetAlertState(EAFLeaperAlertState NewState);

    /** Report a player that this Leaper can currently see. */
    UFUNCTION(BlueprintCallable, Category="Afterfall|Leaper|Alert|Sensing")
    void NotifyPlayerSeen(AActor* PlayerActor);

    /** Report a world-space gunshot or other loud threat location. */
    UFUNCTION(BlueprintCallable, Category="Afterfall|Leaper|Alert|Sensing")
    void NotifyGunshotHeard(FVector WorldLocation, float Loudness = 1.0f);

    /** Blueprint hook for AI Perception or other threat sources. */
    UFUNCTION(BlueprintCallable, Category="Afterfall|Leaper|Alert|Sensing")
    void NotifyThreatSensed(
        FVector WorldLocation,
        EAFLeaperAlertState ThreatState = EAFLeaperAlertState::Alert);

    UFUNCTION(BlueprintPure, Category="Afterfall|Leaper|Alert")
    EAFLeaperAlertState GetAlertState() const { return AlertState; }

    UFUNCTION(BlueprintPure, Category="Afterfall|Leaper|Traversal")
    EAFLeaperTraversalMode GetTraversalMode() const { return TraversalMode; }

    UFUNCTION(BlueprintPure, Category="Afterfall|Leaper|Traversal")
    bool IsSurfaceCrawling() const
    {
        return TraversalMode == EAFLeaperTraversalMode::SurfaceCrawl;
    }

    UPROPERTY(BlueprintAssignable, Category="Afterfall|Leaper|Alert")
    FAFOnLeaperAlertStateChanged OnAlertStateChanged;

    UFUNCTION(BlueprintCallable, Category="Afterfall|Leaper|Weak Points")
    bool ApplyWeakPointDamage(FName WeakPointId, float DamageAmount, FVector HitLocation);

    UFUNCTION(BlueprintPure, Category="Afterfall|Leaper|Weak Points")
    bool IsWeakPointDiscovered(FName WeakPointId) const;

    UFUNCTION(BlueprintPure, Category="Afterfall|Leaper|Weak Points")
    bool IsWeakPointBroken(FName WeakPointId) const;

    UFUNCTION(BlueprintPure, Category="Afterfall|Leaper|Weak Points")
    bool GetWeakPointState(FName WeakPointId, FAFLeaperWeakPointState& OutState) const;

    UPROPERTY(BlueprintAssignable, Category="Afterfall|Leaper|Weak Points")
    FAFOnLeaperWeakPointDiscovered OnWeakPointDiscovered;

    UPROPERTY(BlueprintAssignable, Category="Afterfall|Leaper|Weak Points")
    FAFOnLeaperWeakPointHit OnWeakPointHit;

    UPROPERTY(BlueprintAssignable, Category="Afterfall|Leaper|Weak Points")
    FAFOnLeaperWeakPointBroken OnWeakPointBroken;

protected:
    virtual void BeginPlay() override;
    virtual void Landed(const FHitResult& Hit) override;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing")
    bool bAutoSensePlayer = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0"))
    float PlayerSightRange = 2600.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.01"))
    float SightScanInterval = 0.08f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0"))
    float VisualMemoryDuration = 1.25f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0"))
    float GunshotHearingRange = 3200.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0"))
    float HearingMemoryDuration = 3.5f;

    /** While white/scanning, distant stationary players are intentionally harder to notice. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0"))
    float MovementDetectionSpeed = 35.0f;

    /** Inside this range the Leaper can notice a player even if they freeze. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0"))
    float CloseVisualDetectionRange = 450.0f;

    /** Continuous visual confirmation required before yellow becomes red/attack. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0"))
    float TargetConfirmationTime = 0.55f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0"))
    float AlertMemoryDuration = 5.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing")
    FName HeadBoneName = TEXT("head");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0"))
    float HeadTurnSpeed = 5.5f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0"))
    float ThreatHeadTurnSpeed = 13.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0", ClampMax="180.0"))
    float MaxHeadYaw = 78.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0", ClampMax="90.0"))
    float MaxHeadPitch = 32.0f;

    // The imported Leaper rig can use the opposite local axis. These signs
    // make the head-turn response tunable without changing the skeleton.
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="-1.0", ClampMax="1.0"))
    float HeadYawSign = 1.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="-1.0", ClampMax="1.0"))
    float HeadPitchSign = 1.0f;

    /** Independent white-state predator scan while the body crawls. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0", ClampMax="120.0"))
    float ScanningHeadYaw = 58.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.0", ClampMax="45.0"))
    float ScanningHeadPitch = 6.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Sensing", meta=(ClampMin="0.05"))
    float ScanningHeadSpeed = 0.65f;

    // Autonomous white -> yellow -> red behaviour.
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour")
    bool bEnableAutonomousBehaviour = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour", meta=(ClampMin="0.0"))
    float ScanningMoveSpeed = 165.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour", meta=(ClampMin="0.0"))
    float AttackMoveSpeed = 390.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour", meta=(ClampMin="100.0"))
    float PatrolRadius = 1200.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour", meta=(ClampMin="1.0"))
    float PatrolAcceptanceRadius = 120.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour", meta=(ClampMin="0.1"))
    float PatrolRetargetMin = 2.5f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour", meta=(ClampMin="0.1"))
    float PatrolRetargetMax = 5.0f;

    /** Head snaps first; body deliberately waits before turning toward a suspicious sound. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour", meta=(ClampMin="0.0"))
    float AlertBodyTurnDelay = 0.28f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour", meta=(ClampMin="0.0"))
    float AlertBodyTurnSpeed = 4.5f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour", meta=(ClampMin="1.0"))
    float AttackMoveAcceptanceRadius = 500.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour", meta=(ClampMin="0.05"))
    float AttackMoveRequestInterval = 0.25f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Behaviour", meta=(ClampMin="0.0"))
    float PounceCooldown = 2.25f;

    // Surface traversal is intentionally tag-driven for the first playable map.
    // Add the LeaperClimbable tag to a building actor or mesh component.
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal")
    bool bEnableSurfaceTraversal = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal")
    bool bAllowScanningSurfaceTraversal = true;

    /** Prototype-only convenience: when enabled, any steep WorldStatic surface can be climbed. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal")
    bool bPrototypeClimbAllWorldStatic = false;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal")
    FName ClimbableActorTag = TEXT("LeaperClimbable");

    /** Maximum absolute Z of a surface normal that counts as a wall/steep climb entry. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal", meta=(ClampMin="0.0", ClampMax="0.95"))
    float MaxClimbEntryNormalZ = 0.55f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal", meta=(ClampMin="10.0"))
    float ClimbEntryProbeDistance = 180.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal", meta=(ClampMin="10.0"))
    float SurfaceProbeDistance = 170.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal", meta=(ClampMin="10.0"))
    float EdgeProbeDistance = 155.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal", meta=(ClampMin="0.0"))
    float SurfaceClearance = 8.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal", meta=(ClampMin="10.0"))
    float SurfaceCrawlSpeed = 235.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal", meta=(ClampMin="0.1"))
    float SurfaceNormalInterpSpeed = 10.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal", meta=(ClampMin="0.1"))
    float SurfaceRotationInterpSpeed = 10.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal", meta=(ClampMin="0.0"))
    float SurfaceLostGraceTime = 0.20f;

    /** A positive-up surface above this threshold can hand control back to NavMesh. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal", meta=(ClampMin="0.0", ClampMax="1.0"))
    float WalkableExitNormalZ = 0.72f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal")
    bool bExitToNavOnWalkableSurface = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal", meta=(ClampMin="0.0"))
    float MinSurfaceCrawlTimeBeforeNavExit = 0.30f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Traversal")
    FVector NavigationProjectionExtent = FVector(140.0f, 140.0f, 180.0f);

    // Assign imported Unreal animation assets in BP_LeaperEnemy defaults.
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Animation")
    TObjectPtr<UAnimationAsset> CrawlAnimation;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Animation")
    TObjectPtr<UAnimationAsset> AlertStanceAnimation;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Animation")
    TObjectPtr<UAnimationAsset> AttackCrawlAnimation;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Animation")
    TObjectPtr<UAnimationAsset> PounceAnimation;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper")
    float MinPounceRange = 350.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper")
    float MaxPounceRange = 1800.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper")
    float PounceFlightTime = 0.85f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper")
    float LandingDamage = 35.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper")
    float LandingDamageRadius = 260.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    TObjectPtr<USphereComponent> WeakEyeHitbox;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    TObjectPtr<USphereComponent> WeakFrontLeftHitbox;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    TObjectPtr<USphereComponent> WeakFrontRightHitbox;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    TObjectPtr<USphereComponent> WeakRearLeftHitbox;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    TObjectPtr<USphereComponent> WeakRearRightHitbox;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points")
    TArray<FAFLeaperWeakPointDefinition> WeakPointDefinitions;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points|Visuals")
    TObjectPtr<UMaterialInterface> DiscoveredWeakPointMaterial;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points|Visuals")
    TObjectPtr<UMaterialInterface> HitFlashWeakPointMaterial;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points|Visuals", meta=(ClampMin="0.01"))
    float WeakPointHitFlashDuration = 0.12f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Weak Points|Loot")
    TSubclassOf<AAFLootPickup> WeakPointLootClass;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Visuals")
    FName SignalMaterialSlot = TEXT("LEAP_SIGNAL_Scan_White");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Visuals")
    TObjectPtr<UMaterialInterface> ScanningSignalMaterial;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Visuals")
    TObjectPtr<UMaterialInterface> AlertSignalMaterial;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Leaper|Alert|Visuals")
    TObjectPtr<UMaterialInterface> AttackSignalMaterial;

private:
    bool bPounceInProgress = false;

    UPROPERTY(VisibleInstanceOnly, Category="Afterfall|Leaper|Traversal")
    EAFLeaperTraversalMode TraversalMode = EAFLeaperTraversalMode::Ground;

    FVector CurrentSurfaceNormal = FVector::UpVector;
    FVector CurrentSurfaceTangent = FVector::ForwardVector;
    FRotator MeshBaseRelativeRotation = FRotator::ZeroRotator;
    float SurfaceCrawlStartTime = -BIG_NUMBER;
    float LastSurfaceContactTime = -BIG_NUMBER;
    float SavedGravityScale = 1.0f;
    bool bSavedOrientRotationToMovement = true;

    float SightScanAccumulator = 0.0f;
    float LastVisualTime = -BIG_NUMBER;
    float LastHeardTime = -BIG_NUMBER;
    float LastThreatTime = -BIG_NUMBER;
    bool bHasHeardLocation = false;

    TWeakObjectPtr<AActor> VisualTarget;
    FVector LastHeardLocation = FVector::ZeroVector;
    FRotator HeadBaseLocalRotation = FRotator::ZeroRotator;
    float CurrentHeadYaw = 0.0f;
    float CurrentHeadPitch = 0.0f;
    float ScanClock = 0.0f;
    float VisualLockStartTime = -BIG_NUMBER;
    float BodyTurnStartTime = -BIG_NUMBER;
    float NextPatrolRetargetTime = 0.0f;
    float NextAttackMoveRequestTime = 0.0f;
    float NextPounceAllowedTime = 0.0f;
    bool bHasLastSeenLocation = false;
    FVector LastSeenLocation = FVector::ZeroVector;

    UPROPERTY(VisibleInstanceOnly, Category="Afterfall|Leaper|Alert")
    EAFLeaperAlertState AlertState = EAFLeaperAlertState::Scanning;

    UPROPERTY(VisibleInstanceOnly, Category="Afterfall|Leaper|Weak Points")
    TMap<FName, FAFLeaperWeakPointState> WeakPointStates;

    TMap<FName, FTimerHandle> WeakPointFlashTimers;

    void ConfigureWeakPointHitbox(
        USphereComponent* Hitbox,
        FName BoneName,
        float Radius);

    void InitializeWeakPoints();
    void FindImportedHelperMaterials();
    void ApplyAlertMaterial();

    bool UpdateSurfaceTraversal(float DeltaSeconds);
    bool TryBeginSurfaceCrawl();
    void BeginSurfaceCrawl(const FHitResult& SurfaceHit, const FVector& EntryDirection);
    void UpdateSurfaceCrawl(float DeltaSeconds);
    void EndSurfaceCrawl(bool bResumeNavigation);
    bool TraceForClimbableSurface(
        const FVector& Start,
        const FVector& End,
        FHitResult& OutHit) const;
    bool IsClimbableHit(const FHitResult& Hit) const;
    bool FindSurfaceContact(
        const FVector& CandidateLocation,
        const FVector& MoveDirection,
        FHitResult& OutHit) const;
    FVector ChooseSurfaceCrawlDirection() const;
    float GetSurfaceOffsetForNormal(const FVector& SurfaceNormal) const;
    void ApplySurfaceVisualRotation(
        const FVector& SurfaceForward,
        const FVector& SurfaceNormal,
        float DeltaSeconds);
    bool CanResumeNavigationAt(const FVector& WorldLocation) const;

    void UpdateThreatSensing(float DeltaSeconds);
    void UpdateHeadTurn(float DeltaSeconds);
    void UpdateBehaviourMovement(float DeltaSeconds);
    void UpdateScanningPatrol();
    void UpdateAlertBodyTurn(float DeltaSeconds);
    void UpdateAttackPursuit();
    void StopAIMovement();
    void SetMovementSpeedForState();
    void PlayStateAnimation();
    bool GetCurrentThreatLocation(FVector& OutLocation) const;
    bool HasLineOfSightToPlayer(AActor* PlayerActor) const;
    FVector GetHeadWorldLocation() const;

    FName ResolveWeakPointId(const FHitResult& HitInfo) const;
    const FAFLeaperWeakPointDefinition* FindWeakPointDefinition(FName WeakPointId) const;
    USphereComponent* FindWeakPointHitbox(FName WeakPointId) const;

    void SetWeakPointMaterial(FName WeakPointId, UMaterialInterface* Material);
    void BeginWeakPointFlash(FName WeakPointId);
    void EndWeakPointFlash(FName WeakPointId);
    void BreakWeakPoint(FName WeakPointId, FVector HitLocation);
    void SpawnWeakPointLoot(const FAFLeaperWeakPointDefinition& Definition, FVector HitLocation);
};
