#pragma once

#include "CoreMinimal.h"
#include "Enemies/AFEnemyBase.h"
#include "AFRigEnemyBase.generated.h"

UENUM(BlueprintType)
enum class EAFRigAlertState : uint8
{
    Patrol UMETA(DisplayName="Patrol"),
    Investigating UMETA(DisplayName="Investigating"),
    Combat UMETA(DisplayName="Combat")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
    FAFOnRigAlertStateChanged,
    EAFRigAlertState,
    NewState);

/**
 * Shared autonomous sensing/memory layer for Afterfall machine rigs.
 *
 * Ground, spider and flying rigs inherit the same threat memory:
 * - patrol normally
 * - investigate gunshots / last known positions
 * - confirm visible players and enter combat
 * - fall back to investigation after losing sight
 * - eventually return to patrol
 *
 * Movement and attack style remain specialized in each child class.
 */
UCLASS(Abstract)
class AFTERFALLMOBILE_API AAFRigEnemyBase : public AAFEnemyBase
{
    GENERATED_BODY()

public:
    AAFRigEnemyBase();

    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Afterfall|Rig|Sensing")
    void NotifyGunshotHeard(FVector WorldLocation, float Loudness = 1.0f);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Rig|Sensing")
    void NotifyThreatLocation(FVector WorldLocation);

    UFUNCTION(BlueprintPure, Category="Afterfall|Rig|Sensing")
    EAFRigAlertState GetRigAlertState() const { return RigAlertState; }

    UFUNCTION(BlueprintPure, Category="Afterfall|Rig|Sensing")
    AActor* GetThreatActor() const { return ThreatActor.Get(); }

    UFUNCTION(BlueprintPure, Category="Afterfall|Rig|Sensing")
    bool GetThreatLocation(FVector& OutLocation) const;

    UFUNCTION(BlueprintPure, Category="Afterfall|Rig|Sensing")
    bool HasVisualThreat() const { return ThreatActor.IsValid(); }

    UPROPERTY(BlueprintAssignable, Category="Afterfall|Rig|Sensing")
    FAFOnRigAlertStateChanged OnRigAlertStateChanged;

protected:
    virtual void BeginPlay() override;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Rig|Sensing")
    bool bAutoSensePlayer = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Rig|Sensing", meta=(ClampMin="0.0"))
    float SightRange = 3200.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Rig|Sensing", meta=(ClampMin="0.01"))
    float SightScanInterval = 0.10f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Rig|Sensing", meta=(ClampMin="0.0"))
    float VisualMemoryDuration = 1.6f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Rig|Sensing", meta=(ClampMin="0.0"))
    float HearingRange = 4200.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Rig|Sensing", meta=(ClampMin="0.0"))
    float AlertMemoryDuration = 7.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Rig|Sensing", meta=(ClampMin="0.0"))
    float TargetHeightOffset = 75.0f;

    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Rig|Sensing")
    void OnRigStateVisualChanged(EAFRigAlertState NewState);

    bool HasLineOfSightTo(AActor* TargetActor) const;
    void SetRigAlertState(EAFRigAlertState NewState);

private:
    EAFRigAlertState RigAlertState = EAFRigAlertState::Patrol;
    TWeakObjectPtr<AActor> ThreatActor;
    FVector LastKnownThreatLocation = FVector::ZeroVector;
    bool bHasLastKnownThreatLocation = false;

    float SightAccumulator = 0.0f;
    float LastVisualTime = -BIG_NUMBER;
    float LastThreatTime = -BIG_NUMBER;

    void UpdateThreatSensing(float DeltaSeconds);
};
