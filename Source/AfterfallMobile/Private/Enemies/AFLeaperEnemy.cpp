#include "Enemies/AFLeaperEnemy.h"

#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"

AAFLeaperEnemy::AAFLeaperEnemy()
{
    EnemyId = TEXT("Leaper");
}

bool AAFLeaperEnemy::TryPounceAt(AActor* TargetActor)
{
    if (!TargetActor || bPounceInProgress || !GetWorld())
    {
        return false;
    }

    const FVector Start = GetActorLocation();
    const FVector Target = TargetActor->GetActorLocation();
    const FVector Delta = Target - Start;
    const float HorizontalDistance = FVector(Delta.X, Delta.Y, 0.0f).Size();

    if (HorizontalDistance < MinPounceRange || HorizontalDistance > MaxPounceRange)
    {
        return false;
    }

    const float FlightTime = FMath::Max(0.25f, PounceFlightTime);
    const float GravityZ = GetWorld()->GetGravityZ();

    FVector LaunchVelocity = Delta / FlightTime;
    LaunchVelocity.Z -= 0.5f * GravityZ * FlightTime;

    bPounceInProgress = true;
    GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    LaunchCharacter(LaunchVelocity, true, true);
    return true;
}

void AAFLeaperEnemy::Landed(const FHitResult& Hit)
{
    Super::Landed(Hit);

    if (!bPounceInProgress)
    {
        return;
    }

    bPounceInProgress = false;

    UGameplayStatics::ApplyRadialDamage(
        this,
        LandingDamage,
        GetActorLocation(),
        LandingDamageRadius,
        nullptr,
        TArray<AActor*>(),
        this,
        GetController(),
        true);
}
