#include "Enemies/AFGunnerEnemy.h"

#include "AIController.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "NavigationSystem.h"
#include "TimerManager.h"

AAFGunnerEnemy::AAFGunnerEnemy()
{
    EnemyId = TEXT("SpiderGunner");
}

void AAFGunnerEnemy::BeginPlay()
{
    Super::BeginPlay();

    SpawnOrigin = GetActorLocation();
    FlankSide = FMath::RandBool() ? 1 : -1;
    NextBurstTime = 0.0f;
    NextPatrolMoveTime = 0.0f;
    NextInvestigateMoveTime = 0.0f;
    NextFlankTime = 0.0f;
}

void AAFGunnerEnemy::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    switch (GetRigAlertState())
    {
        case EAFRigAlertState::Patrol:
            SetGroundMoveSpeed(PatrolMoveSpeed);
            UpdatePatrol();
            break;

        case EAFRigAlertState::Investigating:
            SetGroundMoveSpeed(InvestigateMoveSpeed);
            UpdateInvestigation();
            break;

        case EAFRigAlertState::Combat:
            SetGroundMoveSpeed(CombatMoveSpeed);
            UpdateCombat();
            break;

        default:
            break;
    }
}

bool AAFGunnerEnemy::FireBurstAt(AActor* TargetActor)
{
    if (!TargetActor || !GetWorld() || ShotsRemaining > 0)
    {
        return false;
    }

    const float Distance = FVector::Dist(
        GetActorLocation(),
        TargetActor->GetActorLocation());

    if (Distance > MaxWeaponRange || !HasLineOfSightTo(TargetActor))
    {
        return false;
    }

    CurrentBurstTarget = TargetActor;
    ShotsRemaining = FMath::Max(1, BurstShots);
    bUseLeftMuzzle = true;

    FireNextShot();

    if (ShotsRemaining > 0)
    {
        GetWorldTimerManager().SetTimer(
            BurstTimerHandle,
            this,
            &AAFGunnerEnemy::FireNextShot,
            FMath::Max(0.01f, BurstShotInterval),
            true);
    }

    return true;
}

FVector AAFGunnerEnemy::ResolveMuzzleLocation() const
{
    const USkeletalMeshComponent* MeshComp = GetMesh();
    if (MeshComp)
    {
        const FName SocketName =
            bUseLeftMuzzle ? LeftMuzzleSocket : RightMuzzleSocket;

        if (MeshComp->DoesSocketExist(SocketName))
        {
            return MeshComp->GetSocketLocation(SocketName);
        }
    }

    const float Side = bUseLeftMuzzle ? 1.0f : -1.0f;

    return GetActorLocation()
        + GetActorForwardVector() * 120.0f
        + GetActorRightVector() * 55.0f * Side
        + FVector(0.0f, 0.0f, 70.0f);
}

void AAFGunnerEnemy::FireNextShot()
{
    if (!GetWorld() ||
        !CurrentBurstTarget.IsValid() ||
        ShotsRemaining <= 0)
    {
        GetWorldTimerManager().ClearTimer(BurstTimerHandle);
        ShotsRemaining = 0;
        CurrentBurstTarget.Reset();
        return;
    }

    AActor* TargetActor = CurrentBurstTarget.Get();

    if (!HasLineOfSightTo(TargetActor))
    {
        GetWorldTimerManager().ClearTimer(BurstTimerHandle);
        ShotsRemaining = 0;
        CurrentBurstTarget.Reset();
        return;
    }

    const FVector Start = ResolveMuzzleLocation();
    const FVector AimPoint =
        TargetActor->GetActorLocation() + FVector(0.0f, 0.0f, 60.0f);
    const FVector Direction = (AimPoint - Start).GetSafeNormal();
    const FVector End = Start + Direction * MaxWeaponRange;

    FHitResult Hit;
    FCollisionQueryParams Params(
        SCENE_QUERY_STAT(AFGunnerShot),
        true,
        this);
    Params.AddIgnoredActor(this);

    if (GetWorld()->LineTraceSingleByChannel(
            Hit,
            Start,
            End,
            ECC_Visibility,
            Params))
    {
        if (AActor* HitActor = Hit.GetActor())
        {
            UGameplayStatics::ApplyPointDamage(
                HitActor,
                ShotDamage,
                Direction,
                Hit,
                GetController(),
                this,
                nullptr);
        }
    }

    OnGunnerShot(Start, Hit);

    --ShotsRemaining;
    bUseLeftMuzzle = !bUseLeftMuzzle;

    if (ShotsRemaining <= 0)
    {
        GetWorldTimerManager().ClearTimer(BurstTimerHandle);
        CurrentBurstTarget.Reset();
    }
}

void AAFGunnerEnemy::UpdatePatrol()
{
    if (!GetWorld())
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();
    if (Now < NextPatrolMoveTime)
    {
        return;
    }

    NextPatrolMoveTime = Now + FMath::FRandRange(3.5f, 6.5f);

    AAIController* AI = Cast<AAIController>(GetController());
    UNavigationSystemV1* Nav =
        FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());

    if (!AI || !Nav)
    {
        return;
    }

    FNavLocation Point;
    if (Nav->GetRandomReachablePointInRadius(
            SpawnOrigin,
            FMath::Max(100.0f, PatrolRadius),
            Point))
    {
        AI->MoveToLocation(
            Point.Location,
            120.0f,
            true,
            true,
            true,
            false,
            nullptr,
            true);
    }
}

void AAFGunnerEnemy::UpdateInvestigation()
{
    if (!GetWorld())
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();
    if (Now < NextInvestigateMoveTime)
    {
        return;
    }

    NextInvestigateMoveTime = Now + 0.45f;

    FVector ThreatLocation;
    if (!GetThreatLocation(ThreatLocation))
    {
        return;
    }

    if (AAIController* AI = Cast<AAIController>(GetController()))
    {
        AI->MoveToLocation(
            ThreatLocation,
            180.0f,
            true,
            true,
            true,
            false,
            nullptr,
            true);
    }
}

void AAFGunnerEnemy::UpdateCombat()
{
    if (!GetWorld())
    {
        return;
    }

    AActor* TargetActor = GetThreatActor();
    if (!TargetActor)
    {
        UpdateInvestigation();
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();
    const float Distance = FVector::Dist2D(
        GetActorLocation(),
        TargetActor->GetActorLocation());

    if (Now >= NextFlankTime)
    {
        NextFlankTime = Now + FMath::Max(0.25f, FlankRetargetInterval);
        RequestFlankMove(TargetActor);
    }

    if (Distance <= MaxWeaponRange &&
        HasLineOfSightTo(TargetActor) &&
        Now >= NextBurstTime)
    {
        if (FireBurstAt(TargetActor))
        {
            NextBurstTime = Now + FMath::Max(0.05f, BurstCooldown);
        }
    }
}

void AAFGunnerEnemy::RequestFlankMove(AActor* TargetActor)
{
    if (!TargetActor || !GetWorld())
    {
        return;
    }

    AAIController* AI = Cast<AAIController>(GetController());
    UNavigationSystemV1* Nav =
        FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());

    if (!AI || !Nav)
    {
        return;
    }

    FVector ToTarget =
        TargetActor->GetActorLocation() - GetActorLocation();
    ToTarget.Z = 0.0f;

    if (!ToTarget.Normalize())
    {
        return;
    }

    // Alternate sides so the spider rig keeps repositioning instead of
    // marching straight down the player's crosshair.
    FlankSide *= -1;

    const FVector Side =
        FVector::CrossProduct(FVector::UpVector, ToTarget).GetSafeNormal()
        * static_cast<float>(FlankSide);

    const FVector Desired =
        TargetActor->GetActorLocation()
        - ToTarget * FMath::Max(350.0f, DesiredCombatRange)
        + Side * FMath::Max(150.0f, FlankDistance);

    FNavLocation Projected;
    if (Nav->ProjectPointToNavigation(
            Desired,
            Projected,
            FVector(300.0f, 300.0f, 300.0f)))
    {
        AI->MoveToLocation(
            Projected.Location,
            140.0f,
            true,
            true,
            true,
            false,
            nullptr,
            true);
    }
}

void AAFGunnerEnemy::SetGroundMoveSpeed(float NewSpeed)
{
    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->MaxWalkSpeed = FMath::Max(0.0f, NewSpeed);
    }
}
