#include "Enemies/AFBombProjectile.h"

#include "Components/SphereComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"

AAFBombProjectile::AAFBombProjectile()
{
    PrimaryActorTick.bCanEverTick = false;

    CollisionSphere = CreateDefaultSubobject<USphereComponent>(TEXT("CollisionSphere"));
    SetRootComponent(CollisionSphere);
    CollisionSphere->InitSphereRadius(22.0f);
    CollisionSphere->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    CollisionSphere->SetCollisionObjectType(ECC_WorldDynamic);
    CollisionSphere->SetCollisionResponseToAllChannels(ECR_Block);
    CollisionSphere->SetNotifyRigidBodyCollision(true);
    CollisionSphere->OnComponentHit.AddDynamic(
        this,
        &AAFBombProjectile::HandleBombHit);

    ProjectileMovement =
        CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("ProjectileMovement"));
    ProjectileMovement->UpdatedComponent = CollisionSphere;
    ProjectileMovement->InitialSpeed = 0.0f;
    ProjectileMovement->MaxSpeed = 2200.0f;
    ProjectileMovement->ProjectileGravityScale = GravityScale;
    ProjectileMovement->bRotationFollowsVelocity = true;
    ProjectileMovement->bShouldBounce = false;
}

void AAFBombProjectile::BeginPlay()
{
    Super::BeginPlay();

    if (ProjectileMovement)
    {
        ProjectileMovement->ProjectileGravityScale = GravityScale;
    }

    if (GetWorld())
    {
        GetWorldTimerManager().SetTimer(
            FuseTimer,
            this,
            &AAFBombProjectile::Explode,
            FMath::Max(0.05f, FuseSeconds),
            false);
    }
}

void AAFBombProjectile::ArmVelocity(FVector InitialVelocity)
{
    if (ProjectileMovement)
    {
        ProjectileMovement->Velocity = InitialVelocity;
    }
}

void AAFBombProjectile::Explode()
{
    if (bExploded || !GetWorld())
    {
        return;
    }

    bExploded = true;
    GetWorldTimerManager().ClearTimer(FuseTimer);

    TArray<AActor*> IgnoreActors;
    IgnoreActors.Add(this);
    if (AActor* OwnerActor = GetOwner())
    {
        IgnoreActors.Add(OwnerActor);
    }

    UGameplayStatics::ApplyRadialDamage(
        this,
        FMath::Max(0.0f, Damage),
        GetActorLocation(),
        FMath::Max(1.0f, DamageRadius),
        nullptr,
        IgnoreActors,
        GetOwner(),
        GetInstigatorController(),
        true);

    OnBombExploded(GetActorLocation());
    Destroy();
}

void AAFBombProjectile::HandleBombHit(
    UPrimitiveComponent* HitComponent,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComponent,
    FVector NormalImpulse,
    const FHitResult& Hit)
{
    if (OtherActor == GetOwner())
    {
        return;
    }

    Explode();
}
