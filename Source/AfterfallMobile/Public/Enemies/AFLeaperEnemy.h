#pragma once

#include "CoreMinimal.h"
#include "Enemies/AFEnemyBase.h"
#include "AFLeaperEnemy.generated.h"

UCLASS()
class AFTERFALLMOBILE_API AAFLeaperEnemy : public AAFEnemyBase
{
    GENERATED_BODY()

public:
    AAFLeaperEnemy();

    UFUNCTION(BlueprintCallable, Category="Afterfall|Leaper")
    bool TryPounceAt(AActor* TargetActor);

protected:
    virtual void Landed(const FHitResult& Hit) override;

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

private:
    bool bPounceInProgress = false;
};
