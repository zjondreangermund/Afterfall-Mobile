#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Weapons/AFWeaponState.h"
#include "AFWeaponBase.generated.h"

class UStaticMeshComponent;
class USceneComponent;
class UPointLightComponent;
class UParticleSystem;
class USoundBase;
class APawn;

USTRUCT(BlueprintType)
struct FAFWeaponTuning
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ammo", meta=(ClampMin="1")) int32 MagazineCapacity = 30;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ammo", meta=(ClampMin="0")) int32 InitialReserve = 120;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Ammo", meta=(ClampMin="0.01")) float ReloadSeconds = 2.2f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Fire", meta=(ClampMin="1")) float RoundsPerMinute = 500.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Fire") bool bAutomatic = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Damage", meta=(ClampMin="0")) float Damage = 25.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Damage", meta=(ClampMin="100")) float EffectiveRange = 12000.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Recoil", meta=(ClampMin="0")) float PitchRecoil = .35f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Recoil", meta=(ClampMin="0")) float YawRecoil = .12f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Accuracy", meta=(ClampMin="0", ClampMax="10")) float HipSpreadDegrees = .8f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Accuracy", meta=(ClampMin="0", ClampMax="10")) float AimSpreadDegrees = .15f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Heat", meta=(ClampMin="0")) float HeatPerShot = 8.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Heat", meta=(ClampMin="1")) float MaxHeat = 100.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Heat", meta=(ClampMin="0")) float CoolPerSecond = 18.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Heat", meta=(ClampMin="0")) float CoolingDelay = .35f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Heat", meta=(ClampMin="0")) float ResumeHeat = 35.f;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FAFWeaponStateChanged);

UCLASS(Blueprintable)
class AFTERFALLMOBILE_API AAFWeaponBase : public AActor
{
    GENERATED_BODY()
public:
    AAFWeaponBase();
    virtual void Tick(float DeltaSeconds) override;
    UFUNCTION(BlueprintCallable, Category="Afterfall|Weapon") bool TryFire();
    UFUNCTION(BlueprintCallable, Category="Afterfall|Weapon") void StartFire();
    UFUNCTION(BlueprintCallable, Category="Afterfall|Weapon") void StopFire();
    UFUNCTION(BlueprintCallable, Category="Afterfall|Weapon") bool Reload();
    UFUNCTION(BlueprintCallable, Category="Afterfall|Weapon") void CancelReload();
    UFUNCTION(BlueprintCallable, Category="Afterfall|Weapon") void AddReserveAmmo(int32 Amount);
    UFUNCTION(BlueprintCallable, Category="Afterfall|Weapon") void SetAiming(bool bNewAiming);
    UFUNCTION(BlueprintPure, Category="Afterfall|Weapon") int32 GetMagazineAmmo() const { return State.Magazine; }
    UFUNCTION(BlueprintPure, Category="Afterfall|Weapon") int32 GetReserveAmmo() const { return State.Reserve; }
    UFUNCTION(BlueprintPure, Category="Afterfall|Weapon") float GetHeatNormalized() const;
    UFUNCTION(BlueprintPure, Category="Afterfall|Weapon") bool IsReloading() const { return State.Reloading; }
    UFUNCTION(BlueprintPure, Category="Afterfall|Weapon") bool IsOverheated() const { return State.Overheated; }
    UFUNCTION(BlueprintPure, Category="Afterfall|Weapon") FTransform GetMuzzleTransform() const;
    // Called by the character's validated equip/drop path; does not reset ammo or heat.
    void SetEquippedPawn(APawn* Pawn);
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Afterfall|Weapon") FAFWeaponTuning Tuning;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Weapon") FName WeaponId = TEXT("Weapon_Generic");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Afterfall|Weapon") bool bCanBePickedUp = true;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Weapon") TObjectPtr<UStaticMeshComponent> WeaponMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Weapon") TObjectPtr<USceneComponent> MuzzleFallback;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Weapon") TObjectPtr<UPointLightComponent> MuzzleLight;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Weapon") TObjectPtr<UPointLightComponent> HeatIndicator;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Afterfall|Sockets") FName MuzzleSocket = TEXT("Muzzle");
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Afterfall|Effects") TObjectPtr<UParticleSystem> MuzzleEffect;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Afterfall|Effects") TObjectPtr<USoundBase> FireSound;
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Afterfall|Effects") TObjectPtr<USoundBase> ReloadSound;
    UPROPERTY(BlueprintAssignable, Category="Afterfall|Weapon") FAFWeaponStateChanged OnStateChanged;
    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Effects") void OnWeaponFired(const FTransform& Muzzle, const FHitResult& Hit);
    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Effects") void OnReloadStarted();
    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Effects") void OnReloadFinished(bool bCancelled);
    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Effects") void OnAimChanged(bool bNewAiming);
    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Effects") void OnHeatChanged(float NormalizedHeat, bool bLocked);
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    AFWeapon::Rules Rules() const;
    void BroadcastState();
    AFWeapon::State State;
    bool bTriggerHeld = false, bAiming = false;
    float FlashRemaining = 0.f;
};
