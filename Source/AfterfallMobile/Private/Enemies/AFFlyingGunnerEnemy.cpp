#include "Enemies/AFFlyingGunnerEnemy.h"

#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"

AAFFlyingGunnerEnemy::AAFFlyingGunnerEnemy()
{
    EnemyId = TEXT("FlyingGunner");
}

void AAFFlyingGunnerEnemy::BeginPlay()
{
    Super::BeginPlay();

    SpawnOrigin = GetActorLocation();
    OrbitDirection = FMath::RandBool() ? 1 : -1;

    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->GravityScale = 0.0f;
        Movement->SetMovementMode(MOVE_Flying);
        Movement->MaxFlySpeed = PatrolSpeed;
        Movement->BrakingDecelerationFlying = 650.0f;
        Movement->bOrientRotationToMovement = false;
    }
}

void AAFFlyingGunnerEnemy::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    UpdateFlight(DeltaSeconds);
}

bool AAFFlyingGunnerEnemy::FireBurstAt(AActor* TargetActor)
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
            &AAFFlyingGunnerEnemy::FireNextShot,
            FMath::Max(0.01f, BurstShotInterval),
            true);
    }

    return true;
}

void AAFFlyingGunnerEnemy::UpdateFlight(float DeltaSeconds)
{
    if (!GetWorld())
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();

    if (GetRigAlertState() == EAFRigAlertState::Patrol)
    {
        const float T = Now * 0.30f;
        const FVector Desired =
            SpawnOrigin
            + FVector(
                FMath::Cos(T) * PatrolRadius,
                FMath::Sin(T) * PatrolRadius,
                FMath::Sin(T * 1.7f) * PatrolHeightVariation);

        MoveToward(Desired, PatrolSpeed, DeltaSeconds);
        FacePoint(Desired, DeltaSeconds);
        return;
    }

    FVector ThreatLocation;
    if (!GetThreatLocation(ThreatLocation))
    {
        MoveToward(SpawnOrigin, PatrolSpeed, DeltaSeconds);
        return;
    }

    AActor* TargetActor = GetThreatActor();

    if (GetRigAlertState() == EAFRigAlertState::Investigating || !TargetActor)
    {
        const FVector Desired =
            ThreatLocation + FVector(0.0f, 0.0f, CombatAltitude);

        MoveToward(Desired, PatrolSpeed, DeltaSeconds);
        FacePoint(ThreatLocation, DeltaSeconds);
        return;
    }

    FVector Radial = GetActorLocation() - TargetActor->GetActorLocation();
    Radial.Z = 0.0f;

    if (!Radial.Normalize())
    {
        Radial = GetActorForwardVector().GetSafeNormal2D();
    }

    const FVector Tangent =
        FVector::CrossProduct(FVector::UpVector, Radial).GetSafeNormal()
        * static_cast<float>(OrbitDirection);

    const FVector Desired =
        TargetActor->GetActorLocation()
        + Radial * FMath::Max(100.0f, CombatOrbitRadius)
        + Tangent * FMath::Max(0.0f, OrbitLeadDistance)
        + FVector(0.0f, 0.0f, CombatAltitude);

    MoveToward(Desired, CombatSpeed, DeltaSeconds);
    FacePoint(
        TargetActor->GetActorLocation() + FVector(0.0f, 0.0f, 70.0f),
        DeltaSeconds);

    if (Now >= NextBurstTime &&
        FVector::Dist(GetActorLocation(), TargetActor->GetActorLocation()) <= MaxWeaponRange &&
        HasLineOfSightTo(TargetActor))
    {
        if (FireBurstAt(TargetActor))
        {
            NextBurstTime = Now + FMath::Max(0.05f, BurstCooldown);

            // Occasionally reverse the orbit after a burst so the rig feels
            // reactive rather than locked to one circular rail.
            if (FMath::FRand() < 0.30f)
            {
                OrbitDirection *= -1;
            }
        }
    }
}

void AAFFlyingGunnerEnemy::MoveToward(
    const FVector& DesiredLocation,
    float Speed,
    float DeltaSeconds)
{
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    if (!Movement)
    {
        return;
    }

    Movement->MaxFlySpeed = FMath::Max(0.0f, Speed);

    const FVector Direction =
        (DesiredLocation - GetActorLocation()).GetSafeNormal();

    if (!Direction.IsNearlyZero())
    {
        AddMovementInput(Direction, 1.0f, true);
    }
}

void AAFFlyingGunnerEnemy::FacePoint(
    const FVector& WorldPoint,
    float DeltaSeconds)
{
    FVector Direction = WorldPoint - GetActorLocation();

    if (Direction.IsNearlyZero())
    {
        return;
    }

    FRotator Desired = Direction.Rotation();
    Desired.Roll = 0.0f;
    Desired.Pitch = FMath::Clamp(Desired.Pitch, -30.0f, 30.0f);

    SetActorRotation(FMath::RInterpTo(
        GetActorRotation(),
        Desired,
        FMath::Max(0.0f, DeltaSeconds),
        5.5f));
}

FVector AAFFlyingGunnerEnemy::ResolveMuzzleLocation() const
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
        + GetActorForwardVector() * 95.0f
        + GetActorRightVector() * 45.0f * Side
        + FVector(0.0f, 0.0f, -15.0f);
}

void AAFFlyingGunnerEnemy::FireNextShot()
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
        TargetActor->GetActorLocation() + FVector(0.0f, 0.0f, 70.0f);
    const FVector Direction = (AimPoint - Start).GetSafeNormal();
    const FVector End = Start + Direction * MaxWeaponRange;

    FHitResult Hit;
    FCollisionQueryParams Params(
        SCENE_QUERY_STAT(AFFlyingGunnerShot),
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

    OnFlyingGunShot(Start, Hit);

    --ShotsRemaining;
    bUseLeftMuzzle = !bUseLeftMuzzle;

    if (ShotsRemaining <= 0)
    {
        GetWorldTimerManager().ClearTimer(BurstTimerHandle);
        CurrentBurstTarget.Reset();
    }
}
