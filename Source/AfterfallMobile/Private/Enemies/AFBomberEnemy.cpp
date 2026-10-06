#include "Enemies/AFBomberEnemy.h"

#include "Enemies/AFBombProjectile.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"

AAFBomberEnemy::AAFBomberEnemy()
{
    EnemyId = TEXT("FlyingBomber");
    BombClass = AAFBombProjectile::StaticClass();
}

void AAFBomberEnemy::BeginPlay()
{
    Super::BeginPlay();

    SpawnOrigin = GetActorLocation();

    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->GravityScale = 0.0f;
        Movement->SetMovementMode(MOVE_Flying);
        Movement->MaxFlySpeed = PatrolSpeed;
        Movement->BrakingDecelerationFlying = 500.0f;
        Movement->bOrientRotationToMovement = false;
    }
}

void AAFBomberEnemy::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    UpdateFlight(DeltaSeconds);
}

bool AAFBomberEnemy::DropBombAt(AActor* TargetActor)
{
    if (!TargetActor || !GetWorld() || !BombClass)
    {
        return false;
    }

    const float Now = GetWorld()->GetTimeSeconds();
    if (Now < NextBombTime)
    {
        return false;
    }

    const FVector ReleaseLocation = ResolveBombReleaseLocation();
    const FRotator ReleaseRotation = GetActorRotation();

    FActorSpawnParameters Params;
    Params.Owner = this;
    Params.Instigator = this;
    Params.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

    AAFBombProjectile* Bomb = GetWorld()->SpawnActor<AAFBombProjectile>(
        BombClass,
        ReleaseLocation,
        ReleaseRotation,
        Params);

    if (!Bomb)
    {
        return false;
    }

    Bomb->ArmVelocity(
        GetVelocity() + FVector(0.0f, 0.0f, -FMath::Max(0.0f, BombDropSpeed)));

    NextBombTime = Now + FMath::Max(0.1f, BombCooldown);

    FVector Away =
        GetActorLocation() - TargetActor->GetActorLocation();
    Away.Z = 0.0f;

    if (!Away.Normalize())
    {
        Away = GetActorForwardVector().GetSafeNormal2D();
    }

    const float SideSign = FMath::RandBool() ? 1.0f : -1.0f;
    const FVector Side =
        FVector::CrossProduct(FVector::UpVector, Away).GetSafeNormal()
        * SideSign;

    BreakAwayDirection =
        (Away * 0.70f + Side * 0.55f + FVector::UpVector * 0.20f)
        .GetSafeNormal();
    BreakAwayUntil = Now + FMath::Max(0.0f, BreakAwaySeconds);

    OnBombReleased(ReleaseLocation);
    return true;
}

void AAFBomberEnemy::UpdateFlight(float DeltaSeconds)
{
    if (!GetWorld())
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();

    if (GetRigAlertState() == EAFRigAlertState::Patrol)
    {
        const float T = Now * 0.22f;
        const FVector Desired =
            SpawnOrigin
            + FVector(
                FMath::Cos(T) * PatrolRadius,
                FMath::Sin(T) * PatrolRadius,
                FMath::Sin(T * 0.65f) * 90.0f);

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
            ThreatLocation + FVector(0.0f, 0.0f, BombingAltitude);

        MoveToward(Desired, PatrolSpeed, DeltaSeconds);
        FacePoint(ThreatLocation, DeltaSeconds);
        return;
    }

    if (Now < BreakAwayUntil)
    {
        const FVector Desired =
            GetActorLocation()
            + BreakAwayDirection * 1200.0f
            + FVector(0.0f, 0.0f, 180.0f);

        MoveToward(Desired, AttackRunSpeed, DeltaSeconds);
        FacePoint(Desired, DeltaSeconds);
        return;
    }

    const FVector PredictedTarget =
        TargetActor->GetActorLocation()
        + TargetActor->GetVelocity() * FMath::Max(0.0f, TargetLeadSeconds);

    const FVector AttackPoint =
        PredictedTarget + FVector(0.0f, 0.0f, BombingAltitude);

    MoveToward(AttackPoint, AttackRunSpeed, DeltaSeconds);
    FacePoint(PredictedTarget, DeltaSeconds);

    const float HorizontalDistance =
        FVector::Dist2D(GetActorLocation(), PredictedTarget);

    const float HeightAboveTarget =
        GetActorLocation().Z - TargetActor->GetActorLocation().Z;

    if (HorizontalDistance <= FMath::Max(50.0f, BombReleaseRadius) &&
        HeightAboveTarget >= BombingAltitude * 0.55f)
    {
        DropBombAt(TargetActor);
    }
}

void AAFBomberEnemy::MoveToward(
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

void AAFBomberEnemy::FacePoint(
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
    Desired.Pitch = FMath::Clamp(Desired.Pitch, -22.0f, 22.0f);

    SetActorRotation(FMath::RInterpTo(
        GetActorRotation(),
        Desired,
        FMath::Max(0.0f, DeltaSeconds),
        4.0f));
}

FVector AAFBomberEnemy::ResolveBombReleaseLocation() const
{
    const USkeletalMeshComponent* MeshComp = GetMesh();

    if (MeshComp && MeshComp->DoesSocketExist(BombSocket))
    {
        return MeshComp->GetSocketLocation(BombSocket);
    }

    return GetActorLocation()
        - GetActorUpVector() * 45.0f
        + GetActorForwardVector() * 20.0f;
}
