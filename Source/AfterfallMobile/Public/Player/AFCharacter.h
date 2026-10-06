#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AFCharacter.generated.h"

class UCameraComponent;
class USpringArmComponent;
class UAFHealthComponent;
class UAFInventoryComponent;
class AAFWeaponBase;

UCLASS()
class AFTERFALLMOBILE_API AAFCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    AAFCharacter();
    virtual void Tick(float DeltaSeconds) override;

    virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

    UFUNCTION(BlueprintCallable, Category="Afterfall|Combat")
    void FirePrimary();

    UFUNCTION(BlueprintCallable, Category="Afterfall|Combat") void StartPrimaryFire();
    UFUNCTION(BlueprintCallable, Category="Afterfall|Combat") void StopPrimaryFire();
    UFUNCTION(BlueprintCallable, Category="Afterfall|Combat") void ReloadWeapon();
    UFUNCTION(BlueprintCallable, Category="Afterfall|Combat") void StartAiming();
    UFUNCTION(BlueprintCallable, Category="Afterfall|Combat") void StopAiming();
    UFUNCTION(BlueprintCallable, Category="Afterfall|Combat") bool EquipWeapon(AAFWeaponBase* Weapon);
    UFUNCTION(BlueprintCallable, Category="Afterfall|Combat") void DropWeapon();
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Combat") TSubclassOf<AAFWeaponBase> DefaultWeaponClass;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Afterfall|Combat") TObjectPtr<AAFWeaponBase> EquippedWeapon;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Combat") FName WeaponAttachSocket = TEXT("Weapon_R");
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Combat") FTransform WeaponGripOffset;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Combat", meta=(ClampMin="1")) float PickupDistance = 250.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Camera") float AimFOV = 65.f;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Afterfall|Combat") bool bIsAiming = false;
    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Combat") void OnEquippedWeaponChanged(AAFWeaponBase* Weapon);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Movement")
    void MoveForward(float Value);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Movement")
    void MoveRight(float Value);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Camera")
    void LookYaw(float Value);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Camera")
    void LookPitch(float Value);

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Camera")
    TObjectPtr<USpringArmComponent> CameraBoom;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Camera")
    TObjectPtr<UCameraComponent> FollowCamera;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Health")
    TObjectPtr<UAFHealthComponent> HealthComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Inventory")
    TObjectPtr<UAFInventoryComponent> InventoryComponent;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    UFUNCTION() void HandleWeaponOwnerDeath();
    float DefaultFOV = 90.f;
    bool bPreviousControllerYaw = false;
    // Retained for serialized Blueprint compatibility; tune EquippedWeapon.Tuning instead.
    UPROPERTY(meta=(DeprecatedProperty, DeprecationMessage="Set Damage on the weapon Tuning"))
    float PrimaryDamage = 25.0f;

    UPROPERTY(meta=(DeprecatedProperty, DeprecationMessage="Set EffectiveRange on the weapon Tuning"))
    float FireRange = 12000.0f;
};
