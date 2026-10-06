#pragma once

#include "CoreMinimal.h"
#include "Enemies/AFRigEnemyBase.h"
#include "AFBomberEnemy.generated.h"

class AAFBombProjectile;

/**
 * Flying bomb rig: performs overhead attack runs and drops explosive charges
 * ahead of the player's movement instead of copying the gunship's attack.
 */
UCLASS()
class AFTERFALLMOBILE_API AAFBomberEnemy : public AAFRigEnemyBase
{
    GENERATED_BODY()

public:
    AAFBomberEnemy();

    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Afterfall|Bomber")
    bool DropBombAt(AActor* TargetActor);

protected:
    virtual void BeginPlay() override;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomber|Movement", meta=(ClampMin="0.0"))
    float PatrolSpeed = 300.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomber|Movement", meta=(ClampMin="0.0"))
    float AttackRunSpeed = 720.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomber|Movement", meta=(ClampMin="100.0"))
    float PatrolRadius = 1200.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomber|Movement", meta=(ClampMin="100.0"))
    float BombingAltitude = 850.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomber|Movement", meta=(ClampMin="0.0"))
    float TargetLeadSeconds = 0.75f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomber|Movement", meta=(ClampMin="0.0"))
    float BreakAwaySeconds = 1.8f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomber|Weapon", meta=(ClampMin="50.0"))
    float BombReleaseRadius = 260.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomber|Weapon", meta=(ClampMin="0.1"))
    float BombCooldown = 4.5f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomber|Weapon", meta=(ClampMin="0.0"))
    float BombDropSpeed = 220.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomber|Weapon")
    FName BombSocket = TEXT("Bomb_Drop");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomber|Weapon")
    TSubclassOf<AAFBombProjectile> BombClass;

    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Bomber|Effects")
    void OnBombReleased(FVector ReleaseLocation);

private:
    FVector SpawnOrigin = FVector::ZeroVector;
    FVector BreakAwayDirection = FVector::ForwardVector;
    float NextBombTime = 0.0f;
    float BreakAwayUntil = -BIG_NUMBER;

    void UpdateFlight(float DeltaSeconds);
    void MoveToward(const FVector& DesiredLocation, float Speed, float DeltaSeconds);
    void FacePoint(const FVector& WorldPoint, float DeltaSeconds);
    FVector ResolveBombReleaseLocation() const;
};
