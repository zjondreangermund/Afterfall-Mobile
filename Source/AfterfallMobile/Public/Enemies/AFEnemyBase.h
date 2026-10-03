#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AFEnemyBase.generated.h"

class UAFHealthComponent;

UCLASS(Abstract)
class AFTERFALLMOBILE_API AAFEnemyBase : public ACharacter
{
    GENERATED_BODY()

public:
    AAFEnemyBase();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Health")
    TObjectPtr<UAFHealthComponent> HealthComponent;

    UFUNCTION(BlueprintPure, Category="Afterfall|Enemy")
    FName GetEnemyId() const { return EnemyId; }

protected:
    virtual void BeginPlay() override;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Enemy")
    FName EnemyId = TEXT("Enemy");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Enemy")
    float ContactDamage = 10.0f;

    UFUNCTION()
    virtual void HandleDeath();
};
