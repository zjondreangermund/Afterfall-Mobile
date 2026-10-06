#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AFBombProjectile.generated.h"

class USphereComponent;
class UProjectileMovementComponent;

UCLASS()
class AFTERFALLMOBILE_API AAFBombProjectile : public AActor
{
    GENERATED_BODY()

public:
    AAFBombProjectile();

    UFUNCTION(BlueprintCallable, Category="Afterfall|Bomb")
    void ArmVelocity(FVector InitialVelocity);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Bomb")
    void Explode();

protected:
    virtual void BeginPlay() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Bomb")
    TObjectPtr<USphereComponent> CollisionSphere;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Bomb")
    TObjectPtr<UProjectileMovementComponent> ProjectileMovement;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomb", meta=(ClampMin="0.0"))
    float Damage = 55.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomb", meta=(ClampMin="1.0"))
    float DamageRadius = 360.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomb", meta=(ClampMin="0.05"))
    float FuseSeconds = 4.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Bomb", meta=(ClampMin="0.0"))
    float GravityScale = 1.35f;

    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Bomb|Effects")
    void OnBombExploded(FVector ExplosionLocation);

private:
    UFUNCTION()
    void HandleBombHit(
        UPrimitiveComponent* HitComponent,
        AActor* OtherActor,
        UPrimitiveComponent* OtherComponent,
        FVector NormalImpulse,
        const FHitResult& Hit);

    FTimerHandle FuseTimer;
    bool bExploded = false;
};
