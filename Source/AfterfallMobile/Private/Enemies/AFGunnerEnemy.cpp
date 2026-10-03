#include "Enemies/AFGunnerEnemy.h"

#include "Components/SkeletalMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"

AAFGunnerEnemy::AAFGunnerEnemy()
{
    EnemyId = TEXT("Gunner");
}

bool AAFGunnerEnemy::FireBurstAt(AActor* TargetActor)
{
    if (!TargetActor || !GetWorld() || ShotsRemaining > 0)
    {
        return false;
    }

    const float Distance = FVector::Dist(GetActorLocation(), TargetActor->GetActorLocation());
    if (Distance > MaxWeaponRange)
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
            BurstShotInterval,
            true);
    }

    return true;
}

FVector AAFGunnerEnemy::ResolveMuzzleLocation() const
{
    const USkeletalMeshComponent* MeshComp = GetMesh();
    if (MeshComp)
    {
        const FName SocketName = bUseLeftMuzzle ? LeftMuzzleSocket : RightMuzzleSocket;
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
    if (!GetWorld() || !CurrentBurstTarget.IsValid() || ShotsRemaining <= 0)
    {
        GetWorldTimerManager().ClearTimer(BurstTimerHandle);
        ShotsRemaining = 0;
        CurrentBurstTarget.Reset();
        return;
    }

    AActor* TargetActor = CurrentBurstTarget.Get();
    const FVector Start = ResolveMuzzleLocation();
    const FVector AimPoint = TargetActor->GetActorLocation();
    const FVector Direction = (AimPoint - Start).GetSafeNormal();
    const FVector End = Start + Direction * MaxWeaponRange;

    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(AFGunnerShot), true, this);

    if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params))
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

    --ShotsRemaining;
    bUseLeftMuzzle = !bUseLeftMuzzle;

    if (ShotsRemaining <= 0)
    {
        GetWorldTimerManager().ClearTimer(BurstTimerHandle);
        CurrentBurstTarget.Reset();
    }
}
