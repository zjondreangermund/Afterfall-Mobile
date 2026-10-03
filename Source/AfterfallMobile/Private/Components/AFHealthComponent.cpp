#include "Components/AFHealthComponent.h"

UAFHealthComponent::UAFHealthComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UAFHealthComponent::BeginPlay()
{
    Super::BeginPlay();

    CurrentHealth = MaxHealth;

    if (AActor* Owner = GetOwner())
    {
        Owner->OnTakeAnyDamage.AddDynamic(this, &UAFHealthComponent::HandleOwnerDamaged);
    }

    OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);
}

void UAFHealthComponent::RestoreFullHealth()
{
    CurrentHealth = MaxHealth;
    OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);
}

void UAFHealthComponent::HandleOwnerDamaged(
    AActor* DamagedActor,
    float Damage,
    const UDamageType* DamageType,
    AController* InstigatedBy,
    AActor* DamageCauser)
{
    if (Damage <= 0.0f || IsDead())
    {
        return;
    }

    CurrentHealth = FMath::Clamp(CurrentHealth - Damage, 0.0f, MaxHealth);
    OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);

    if (IsDead())
    {
        OnDeath.Broadcast();
    }
}
