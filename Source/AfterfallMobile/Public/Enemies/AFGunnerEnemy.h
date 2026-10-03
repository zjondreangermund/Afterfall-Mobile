#pragma once

#include "CoreMinimal.h"
#include "Enemies/AFEnemyBase.h"
#include "AFGunnerEnemy.generated.h"

UCLASS()
class AFTERFALLMOBILE_API AAFGunnerEnemy : public AAFEnemyBase
{
    GENERATED_BODY()

public:
    AAFGunnerEnemy();

    UFUNCTION(BlueprintCallable, Category="Afterfall|Gunner")
    bool FireBurstAt(AActor* TargetActor);

protected:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner", meta=(ClampMin="1.0"))
    float ShotDamage = 12.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner", meta=(ClampMin="100.0"))
    float MaxWeaponRange = 2600.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner", meta=(ClampMin="1"))
    int32 BurstShots = 3;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner", meta=(ClampMin="0.01"))
    float BurstShotInterval = 0.12f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner")
    FName LeftMuzzleSocket = TEXT("Muzzle_L");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Gunner")
    FName RightMuzzleSocket = TEXT("Muzzle_R");

private:
    TWeakObjectPtr<AActor> CurrentBurstTarget;
    int32 ShotsRemaining = 0;
    bool bUseLeftMuzzle = true;
    FTimerHandle BurstTimerHandle;

    void FireNextShot();
    FVector ResolveMuzzleLocation() const;
};
