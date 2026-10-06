#include "Enemies/AFRigEnemyBase.h"

#include "AIController.h"
#include "Components/AFHealthComponent.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

AAFRigEnemyBase::AAFRigEnemyBase()
{
    PrimaryActorTick.bCanEverTick = true;
    AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;
}

void AAFRigEnemyBase::BeginPlay()
{
    Super::BeginPlay();

    if (!GetController())
    {
        SpawnDefaultController();
    }

    SightAccumulator = SightScanInterval;
    LastVisualTime = -BIG_NUMBER;
    LastThreatTime = -BIG_NUMBER;
    SetRigAlertState(EAFRigAlertState::Patrol);
}

void AAFRigEnemyBase::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    UpdateThreatSensing(DeltaSeconds);
}

void AAFRigEnemyBase::NotifyGunshotHeard(
    FVector WorldLocation,
    float Loudness)
{
    if (!GetWorld())
    {
        return;
    }

    const float EffectiveRange =
        HearingRange * FMath::Clamp(Loudness, 0.25f, 4.0f);

    if (EffectiveRange <= 0.0f ||
        FVector::DistSquared(GetActorLocation(), WorldLocation) >
            FMath::Square(EffectiveRange))
    {
        return;
    }

    LastKnownThreatLocation = WorldLocation;
    bHasLastKnownThreatLocation = true;
    LastThreatTime = GetWorld()->GetTimeSeconds();

    if (RigAlertState != EAFRigAlertState::Combat)
    {
        SetRigAlertState(EAFRigAlertState::Investigating);
    }
}

void AAFRigEnemyBase::NotifyThreatLocation(FVector WorldLocation)
{
    if (!GetWorld())
    {
        return;
    }

    LastKnownThreatLocation = WorldLocation;
    bHasLastKnownThreatLocation = true;
    LastThreatTime = GetWorld()->GetTimeSeconds();

    if (RigAlertState == EAFRigAlertState::Patrol)
    {
        SetRigAlertState(EAFRigAlertState::Investigating);
    }
}

bool AAFRigEnemyBase::GetThreatLocation(FVector& OutLocation) const
{
    if (ThreatActor.IsValid())
    {
        OutLocation = ThreatActor->GetActorLocation();
        return true;
    }

    if (bHasLastKnownThreatLocation)
    {
        OutLocation = LastKnownThreatLocation;
        return true;
    }

    return false;
}

bool AAFRigEnemyBase::HasLineOfSightTo(AActor* TargetActor) const
{
    if (!GetWorld() || !TargetActor)
    {
        return false;
    }

    const FVector Start =
        GetActorLocation() + FVector(0.0f, 0.0f, TargetHeightOffset);
    const FVector End =
        TargetActor->GetActorLocation() +
        FVector(0.0f, 0.0f, TargetHeightOffset);

    FCollisionQueryParams Params(
        SCENE_QUERY_STAT(AFRigSight),
        true,
        this);
    Params.AddIgnoredActor(this);

    FHitResult Hit;
    if (!GetWorld()->LineTraceSingleByChannel(
            Hit,
            Start,
            End,
            ECC_Visibility,
            Params))
    {
        return true;
    }

    return Hit.GetActor() == TargetActor;
}

void AAFRigEnemyBase::SetRigAlertState(EAFRigAlertState NewState)
{
    if (RigAlertState == NewState)
    {
        return;
    }

    RigAlertState = NewState;
    OnRigStateVisualChanged(NewState);
    OnRigAlertStateChanged.Broadcast(NewState);
}

void AAFRigEnemyBase::UpdateThreatSensing(float DeltaSeconds)
{
    if (!GetWorld())
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();

    if (bAutoSensePlayer)
    {
        SightAccumulator += FMath::Max(0.0f, DeltaSeconds);

        if (SightAccumulator >= FMath::Max(0.01f, SightScanInterval))
        {
            SightAccumulator = 0.0f;

            APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
            if (PlayerPawn && PlayerPawn != this)
            {
                const float DistSq = FVector::DistSquared(
                    GetActorLocation(),
                    PlayerPawn->GetActorLocation());

                if (DistSq <= FMath::Square(SightRange) &&
                    HasLineOfSightTo(PlayerPawn))
                {
                    ThreatActor = PlayerPawn;
                    LastKnownThreatLocation = PlayerPawn->GetActorLocation();
                    bHasLastKnownThreatLocation = true;
                    LastVisualTime = Now;
                    LastThreatTime = Now;
                    SetRigAlertState(EAFRigAlertState::Combat);
                }
            }
        }
    }

    if (ThreatActor.IsValid() &&
        Now - LastVisualTime > FMath::Max(0.0f, VisualMemoryDuration))
    {
        ThreatActor.Reset();
        SetRigAlertState(EAFRigAlertState::Investigating);
    }

    if (RigAlertState == EAFRigAlertState::Investigating &&
        Now - LastThreatTime > FMath::Max(0.0f, AlertMemoryDuration))
    {
        bHasLastKnownThreatLocation = false;
        SetRigAlertState(EAFRigAlertState::Patrol);
    }
}
