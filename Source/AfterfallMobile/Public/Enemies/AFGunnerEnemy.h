#pragma once

#include "CoreMinimal.h"
#include "Enemies/AFRigEnemyBase.h"
#include "AFGunnerEnemy.generated.h"

/**
 * Ground/spider gun rig.
 *
 * Designed for the spider-like armed rig:
 * - patrols on NavMesh
 * - reacts to gunshots
 * - investigates last known positions
 * - flanks instead of walking straight at the player
 * - fires alternating-muzzle bursts while repositioning
 */
UCLASS()
class AFTERFALLMOBILE_API AAFGunnerEnemy : public AAFRigEnemyBase
{
    GENERATED_BODY()

public:
    AAFGunnerEnemy();

    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Afterfall|Gunner")
    bool FireBurstAt(AActor* TargetActor);

protected:
    virtual void BeginPlay() override;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Weapon", meta=(ClampMin="1.0"))
    float ShotDamage = 12.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Weapon", meta=(ClampMin="100.0"))
    float MaxWeaponRange = 2800.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Weapon", meta=(ClampMin="1"))
    int32 BurstShots = 4;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Weapon", meta=(ClampMin="0.01"))
    float BurstShotInterval = 0.10f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Weapon", meta=(ClampMin="0.05"))
    float BurstCooldown = 0.85f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Weapon")
    FName LeftMuzzleSocket = TEXT("Muzzle_L");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Weapon")
    FName RightMuzzleSocket = TEXT("Muzzle_R");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Movement", meta=(ClampMin="0.0"))
    float PatrolMoveSpeed = 180.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Movement", meta=(ClampMin="0.0"))
    float InvestigateMoveSpeed = 220.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Movement", meta=(ClampMin="0.0"))
    float CombatMoveSpeed = 300.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Movement", meta=(ClampMin="100.0"))
    float PatrolRadius = 1100.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Movement", meta=(ClampMin="100.0"))
    float DesiredCombatRange = 1450.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Movement", meta=(ClampMin="100.0"))
    float FlankDistance = 800.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner|Movement", meta=(ClampMin="0.1"))
    float FlankRetargetInterval = 2.1f;

    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Gunner|Effects")
    void OnGunnerShot(FVector MuzzleLocation, const FHitResult& Hit);

private:
    TWeakObjectPtr<AActor> CurrentBurstTarget;
    int32 ShotsRemaining = 0;
    bool bUseLeftMuzzle = true;
    FTimerHandle BurstTimerHandle;

    FVector SpawnOrigin = FVector::ZeroVector;
    float NextBurstTime = 0.0f;
    float NextPatrolMoveTime = 0.0f;
    float NextInvestigateMoveTime = 0.0f;
    float NextFlankTime = 0.0f;
    int32 FlankSide = 1;

    void FireNextShot();
    FVector ResolveMuzzleLocation() const;

    void UpdatePatrol();
    void UpdateInvestigation();
    void UpdateCombat();
    void RequestFlankMove(AActor* TargetActor);
    void SetGroundMoveSpeed(float NewSpeed);
};
