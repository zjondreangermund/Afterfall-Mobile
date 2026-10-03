#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AFHealthComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FAFOnHealthChanged, float, CurrentHealth, float, MaxHealth);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FAFOnDeath);

UCLASS(ClassGroup=(Afterfall), meta=(BlueprintSpawnableComponent))
class AFTERFALLMOBILE_API UAFHealthComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UAFHealthComponent();

    UFUNCTION(BlueprintPure, Category="Afterfall|Health")
    float GetCurrentHealth() const { return CurrentHealth; }

    UFUNCTION(BlueprintPure, Category="Afterfall|Health")
    float GetMaxHealth() const { return MaxHealth; }

    UFUNCTION(BlueprintPure, Category="Afterfall|Health")
    bool IsDead() const { return CurrentHealth <= 0.0f; }

    UFUNCTION(BlueprintCallable, Category="Afterfall|Health")
    void RestoreFullHealth();

    UPROPERTY(BlueprintAssignable, Category="Afterfall|Health")
    FAFOnHealthChanged OnHealthChanged;

    UPROPERTY(BlueprintAssignable, Category="Afterfall|Health")
    FAFOnDeath OnDeath;

protected:
    virtual void BeginPlay() override;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Health", meta=(ClampMin="1.0"))
    float MaxHealth = 100.0f;

private:
    UPROPERTY(VisibleInstanceOnly, Category="Afterfall|Health")
    float CurrentHealth = 100.0f;

    UFUNCTION()
    void HandleOwnerDamaged(
        AActor* DamagedActor,
        float Damage,
        const class UDamageType* DamageType,
        class AController* InstigatedBy,
        AActor* DamageCauser);
};
