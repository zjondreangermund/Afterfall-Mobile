#include "Enemies/AFEnemyBase.h"

#include "Components/AFHealthComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

AAFEnemyBase::AAFEnemyBase()
{
    PrimaryActorTick.bCanEverTick = false;

    HealthComponent = CreateDefaultSubobject<UAFHealthComponent>(TEXT("HealthComponent"));

    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0.0f, 360.0f, 0.0f);
}

void AAFEnemyBase::BeginPlay()
{
    Super::BeginPlay();

    if (HealthComponent)
    {
        HealthComponent->OnDeath.AddDynamic(this, &AAFEnemyBase::HandleDeath);
    }
}

void AAFEnemyBase::HandleDeath()
{
    SetActorEnableCollision(false);
    GetCharacterMovement()->DisableMovement();
    SetLifeSpan(4.0f);
}
