#pragma once

#include "CoreMinimal.h"
#include "TimerManager.h"
#include "Enemies/AFEnemyBase.h"
#include "AFLeaperEnemy.generated.h"

class AAFLootPickup;
class UMaterialInterface;
class USphereComponent;

UENUM(BlueprintType)
enum class EAFLeaperAlertState : uint8
{
    Scanning UMETA(DisplayName="Scanning"),
    Alert UMETA(DisplayName="Alert"),
    Attacking UMETA(DisplayName="Attacking")
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

    void UpdateThreatSensing(float DeltaSeconds);
    void UpdateHeadTurn(float DeltaSeconds);
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
