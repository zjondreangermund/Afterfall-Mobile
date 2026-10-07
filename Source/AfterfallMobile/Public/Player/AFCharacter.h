#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AFCharacter.generated.h"

class UCameraComponent;
class USpringArmComponent;
class UAFHealthComponent;
class UAFInventoryComponent;
class AAFWeaponBase;
class UAnimSequenceBase;
class UAnimInstance;

UENUM(BlueprintType)
enum class EAFTraversalState : uint8
{
    None UMETA(DisplayName="Normal"),
    Vaulting UMETA(DisplayName="Vaulting"),
    Mantling UMETA(DisplayName="Mantling"),
    Hanging UMETA(DisplayName="Ledge Hang")
};

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

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Combat")
    TSubclassOf<AAFWeaponBase> DefaultWeaponClass;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Afterfall|Combat")
    TObjectPtr<AAFWeaponBase> EquippedWeapon;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Combat")
    FName WeaponAttachSocket = TEXT("Weapon_R");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Combat")
    FTransform WeaponGripOffset;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Combat", meta=(ClampMin="1"))
    float PickupDistance = 250.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Camera")
    float AimFOV = 65.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Camera|Shoulder", meta=(ClampMin="50"))
    float NormalCameraArmLength = 260.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Camera|Shoulder", meta=(ClampMin="50"))
    float AimCameraArmLength = 240.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Camera|Shoulder", meta=(ClampMin="0"))
    float ShoulderOffsetY = 65.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Camera|Shoulder")
    float NormalCameraHeight = 65.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Camera|Shoulder")
    float AimCameraHeight = 65.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Camera|Shoulder", meta=(ClampMin="0.1"))
    float CameraInterpSpeed = 12.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Camera|AimPitch", meta=(ClampMin="-89", ClampMax="0"))
    float MinAimPitch = -55.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Camera|AimPitch", meta=(ClampMin="0", ClampMax="89"))
    float MaxAimPitch = 55.f;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Afterfall|Combat")
    bool bIsAiming = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Afterfall|Combat")
    float AimPitch = 0.f;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Afterfall|Combat")
    bool bLeftShoulder = false;

    UFUNCTION(BlueprintCallable, Category="Afterfall|Combat")
    void ToggleShoulder();

    UFUNCTION(BlueprintPure, Category="Afterfall|Combat")
    bool IsLeftShoulder() const { return bLeftShoulder; }

    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Combat")
    void OnEquippedWeaponChanged(AAFWeaponBase* Weapon);

    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Combat")
    void OnShoulderChanged(bool bNowLeftShoulder);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Movement")
    void MoveForward(float Value);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Movement")
    void MoveRight(float Value);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Camera")
    void LookYaw(float Value);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Camera")
    void LookPitch(float Value);

    // Contextual traversal. Space jumps normally, but vaults/mantles when a
    // valid obstacle is directly ahead. Falling characters can auto-grab ledges.
    UFUNCTION(BlueprintCallable, Category="Afterfall|Traversal")
    void TraversalJumpPressed();

    UFUNCTION(BlueprintCallable, Category="Afterfall|Traversal")
    void TraversalJumpReleased();

    UFUNCTION(BlueprintCallable, Category="Afterfall|Traversal")
    void DropFromLedge();

    UFUNCTION(BlueprintCallable, Category="Afterfall|Traversal")
    bool TryContextTraversal();

    UFUNCTION(BlueprintPure, Category="Afterfall|Traversal")
    EAFTraversalState GetTraversalState() const { return TraversalState; }

    UFUNCTION(BlueprintPure, Category="Afterfall|Traversal")
    bool IsHanging() const { return TraversalState == EAFTraversalState::Hanging; }

    UFUNCTION(BlueprintPure, Category="Afterfall|Traversal")
    bool IsTraversalActive() const { return TraversalState != EAFTraversalState::None; }

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Afterfall|Traversal|Animation")
    bool bIsInAir = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Afterfall|Traversal|Animation")
    float VerticalVelocity = 0.0f;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Afterfall|Traversal|Animation")
    float TraversalAlpha = 0.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal|Animation")
    bool bHideWeaponDuringTraversal = true;

    // Existing Manny rifle jump assets are used automatically so normal jumps
    // no longer play the ground locomotion pose in mid-air.
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal|Animation|Jump")
    TSoftObjectPtr<UAnimSequenceBase> JumpStartAnimation;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal|Animation|Jump")
    TSoftObjectPtr<UAnimSequenceBase> JumpFallLoopAnimation;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal|Animation|Jump")
    TSoftObjectPtr<UAnimSequenceBase> JumpLandAnimation;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal|Animation|Jump", meta=(ClampMin="0.1"))
    float JumpVisualPlayRate = 1.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal")
    bool bAutoLedgeGrab = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal", meta=(ClampMin="40.0"))
    float TraversalProbeDistance = 135.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal", meta=(ClampMin="10.0"))
    float MinTraversalObstacleHeight = 32.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal", meta=(ClampMin="40.0"))
    float VaultMaxHeight = 105.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal", meta=(ClampMin="80.0"))
    float MantleMaxHeight = 215.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal", meta=(ClampMin="0.05"))
    float VaultDuration = 0.46f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal", meta=(ClampMin="0.05"))
    float MantleDuration = 0.58f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal", meta=(ClampMin="10.0"))
    float VaultLandingForwardDistance = 155.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal", meta=(ClampMin="20.0"))
    float LedgeGrabForwardDistance = 95.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal")
    float LedgeTopMinRelativeHeight = 20.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal")
    float LedgeTopMaxRelativeHeight = 145.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal", meta=(ClampMin="10.0"))
    float HangBodyDrop = 72.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal", meta=(ClampMin="0.0"))
    float HangShimmySpeed = 115.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Traversal")
    bool bAutoSpawnTraversalTestCourseInEditor = true;

    UFUNCTION(BlueprintImplementableEvent, Category="Afterfall|Traversal")
    void OnTraversalStateChanged(EAFTraversalState NewState);

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
    virtual void Landed(const FHitResult& Hit) override;

    UFUNCTION()
    void HandleWeaponOwnerDeath();

    float DefaultFOV = 90.f;
    bool bPreviousControllerYaw = false;
    bool bPreviousOrientRotationToMovement = true;

    UPROPERTY(meta=(DeprecatedProperty, DeprecationMessage="Set Damage on the weapon Tuning"))
    float PrimaryDamage = 25.0f;

    UPROPERTY(meta=(DeprecatedProperty, DeprecationMessage="Set EffectiveRange on the weapon Tuning"))
    float FireRange = 12000.0f;

private:
    EAFTraversalState TraversalState = EAFTraversalState::None;

    FVector TraversalStartLocation = FVector::ZeroVector;
    FVector TraversalTargetLocation = FVector::ZeroVector;
    FRotator TraversalStartRotation = FRotator::ZeroRotator;
    FRotator TraversalTargetRotation = FRotator::ZeroRotator;
    float TraversalElapsed = 0.f;
    float TraversalDurationActive = 0.5f;
    float TraversalArcHeight = 0.f;

    FVector HangingWallNormal = FVector::ZeroVector;
    FVector HangingLedgeTop = FVector::ZeroVector;

    float MoveForwardInput = 0.f;
    float MoveRightInput = 0.f;
    float LedgeGrabScanCooldown = 0.f;

    bool bJumpVisualActive = false;
    bool bFallLoopVisualActive = false;
    TSubclassOf<UAnimInstance> SavedLocomotionAnimClass;
    FTimerHandle JumpVisualTimer;

    void UpdateTraversal(float DeltaSeconds);
    void UpdateHanging(float DeltaSeconds);
    bool TryAutoGrabLedge();
    bool FindObstacleTop(
        float ForwardDistance,
        FHitResult& OutWallHit,
        FHitResult& OutTopHit,
        float& OutObstacleHeight) const;
    bool FindVaultLanding(
        const FHitResult& WallHit,
        FVector& OutLandingLocation) const;
    bool CanOccupyCapsuleAt(const FVector& WorldLocation) const;
    void StartTraversalMove(
        EAFTraversalState NewState,
        const FVector& TargetLocation,
        const FRotator& TargetRotation,
        float Duration,
        float ArcHeight);
    void EnterLedgeHang(
        const FHitResult& WallHit,
        const FHitResult& TopHit);
    void ClimbFromLedge();
    void FinishTraversalMove();
    void SetTraversalWeaponStowed(bool bStowed);
    bool PlayFullBodySequence(TSoftObjectPtr<UAnimSequenceBase> Sequence, bool bLoop);
    void RestoreLocomotionAnimationBlueprint();
    FVector GetTraversalForward() const;
};
