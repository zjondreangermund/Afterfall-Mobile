#pragma once

#include "CoreMinimal.h"
#include "Enemies/AFRigEnemyBase.h"
#include "AFFlyingGunnerEnemy.generated.h"

/**
 * Flying gun rig: an agile aerial hunter that orbits and strafes the player
 * while firing alternating-muzzle bursts.
 */
UCLASS()
class AFTERFALLMOBILE_API AAFFlyingGunnerEnemy : public AAFRigEnemyBase
{
    GENERATED_BODY()

public:
    AAFFlyingGunnerEnemy();

    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Afterfall|FlyingGunner")
    bool FireBurstAt(AActor* TargetActor);

protected:
    virtual void BeginPlay() override;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Movement", meta=(ClampMin="0.0"))
    float PatrolSpeed = 320.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Movement", meta=(ClampMin="0.0"))
    float CombatSpeed = 560.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Movement", meta=(ClampMin="100.0"))
    float PatrolRadius = 900.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Movement", meta=(ClampMin="0.0"))
    float PatrolHeightVariation = 180.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Movement", meta=(ClampMin="100.0"))
    float CombatOrbitRadius = 1250.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Movement", meta=(ClampMin="0.0"))
    float CombatAltitude = 650.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Movement", meta=(ClampMin="0.0"))
    float OrbitLeadDistance = 420.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Weapon", meta=(ClampMin="1.0"))
    float ShotDamage = 10.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Weapon", meta=(ClampMin="100.0"))
    float MaxWeaponRange = 3600.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Weapon", meta=(ClampMin="1"))
    int32 BurstShots = 5;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Weapon", meta=(ClampMin="0.01"))
    float BurstShotInterval = 0.085f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Weapon", meta=(ClampMin="0.05"))
    float BurstCooldown = 0.95f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Weapon")
    FName LeftMuzzleSocket = TEXT("Muzzle_L");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|FlyingGunner|Weapon")
    FName RightMuzzleSocket = TEXT("Muzzle_R");

    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|FlyingGunner|Effects")
    void OnFlyingGunShot(FVector MuzzleLocation, const FHitResult& Hit);

private:
    FVector SpawnOrigin = FVector::ZeroVector;
    int32 OrbitDirection = 1;
    float NextBurstTime = 0.0f;

    TWeakObjectPtr<AActor> CurrentBurstTarget;
    int32 ShotsRemaining = 0;
    bool bUseLeftMuzzle = true;
    FTimerHandle BurstTimerHandle;

    void UpdateFlight(float DeltaSeconds);
    void MoveToward(const FVector& DesiredLocation, float Speed, float DeltaSeconds);
    void FacePoint(const FVector& WorldPoint, float DeltaSeconds);
    FVector ResolveMuzzleLocation() const;
    void FireNextShot();
};
