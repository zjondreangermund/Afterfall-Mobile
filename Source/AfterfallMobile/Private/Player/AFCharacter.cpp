#include "Player/AFCharacter.h"

#include "Camera/CameraComponent.h"
#include "Components/AFHealthComponent.h"
#include "Weapons/AFHoundWeapon.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Inventory/AFInventoryComponent.h"
#include "Kismet/GameplayStatics.h"

AAFCharacter::AAFCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    DefaultWeaponClass = AAFHoundWeapon::StaticClass();

    bUseControllerRotationPitch = false;
    bUseControllerRotationYaw = false;
    bUseControllerRotationRoll = false;

    // Free-look traversal. Aiming temporarily switches to controller-yaw facing
    // so strafing/backpedalling behaves like a third-person shooter.
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0.0f, 540.0f, 0.0f);

    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->TargetArmLength = NormalCameraArmLength;
    CameraBoom->SocketOffset = FVector(0.f, ShoulderOffsetY, NormalCameraHeight);
    CameraBoom->bUsePawnControlRotation = true;

    FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
    FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    FollowCamera->bUsePawnControlRotation = false;

    HealthComponent = CreateDefaultSubobject<UAFHealthComponent>(TEXT("HealthComponent"));
    InventoryComponent = CreateDefaultSubobject<UAFInventoryComponent>(TEXT("InventoryComponent"));
}

void AAFCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &AAFCharacter::MoveForward);
    PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &AAFCharacter::MoveRight);
    PlayerInputComponent->BindAxis(TEXT("Turn"), this, &AAFCharacter::LookYaw);
    PlayerInputComponent->BindAxis(TEXT("LookUp"), this, &AAFCharacter::LookPitch);

    PlayerInputComponent->BindAction(TEXT("Fire"), IE_Pressed, this, &AAFCharacter::StartPrimaryFire);
    PlayerInputComponent->BindAction(TEXT("Fire"), IE_Released, this, &AAFCharacter::StopPrimaryFire);
    PlayerInputComponent->BindAction(TEXT("Reload"), IE_Pressed, this, &AAFCharacter::ReloadWeapon);
    PlayerInputComponent->BindAction(TEXT("Aim"), IE_Pressed, this, &AAFCharacter::StartAiming);
    PlayerInputComponent->BindAction(TEXT("Aim"), IE_Released, this, &AAFCharacter::StopAiming);
    PlayerInputComponent->BindAction(TEXT("SwitchShoulder"), IE_Pressed, this, &AAFCharacter::ToggleShoulder);
}

void AAFCharacter::MoveForward(float Value)
{
    if (Controller && !FMath::IsNearlyZero(Value))
    {
        const FRotator Rotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
        AddMovementInput(FRotationMatrix(Rotation).GetUnitAxis(EAxis::X), Value);
    }
}

void AAFCharacter::MoveRight(float Value)
{
    if (Controller && !FMath::IsNearlyZero(Value))
    {
        const FRotator Rotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
        AddMovementInput(FRotationMatrix(Rotation).GetUnitAxis(EAxis::Y), Value);
    }
}

void AAFCharacter::LookYaw(float Value)
{
    AddControllerYawInput(Value);
}

void AAFCharacter::LookPitch(float Value)
{
    AddControllerPitchInput(Value);
}

void AAFCharacter::FirePrimary()
{
    if (IsValid(EquippedWeapon) && !HealthComponent->IsDead())
    {
        EquippedWeapon->TryFire();
    }
}

void AAFCharacter::BeginPlay()
{
    Super::BeginPlay();

    DefaultFOV = FollowCamera->FieldOfView;

    // Make the native camera framing authoritative from the first frame.
    CameraBoom->TargetArmLength = NormalCameraArmLength;
    CameraBoom->SocketOffset = FVector(
        0.f,
        bLeftShoulder ? -ShoulderOffsetY : ShoulderOffsetY,
        NormalCameraHeight);

    HealthComponent->OnDeath.AddDynamic(this, &AAFCharacter::HandleWeaponOwnerDeath);

    if (DefaultWeaponClass && GetWorld())
    {
        FActorSpawnParameters Params;
        Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

        if (AAFWeaponBase* Weapon = GetWorld()->SpawnActor<AAFWeaponBase>(
                DefaultWeaponClass, GetActorTransform(), Params))
        {
            if (!EquipWeapon(Weapon))
            {
                Weapon->Destroy();
            }
        }
    }
}

void AAFCharacter::EndPlay(const EEndPlayReason::Type Reason)
{
    if (IsValid(EquippedWeapon))
    {
        EquippedWeapon->StopFire();
        EquippedWeapon->Destroy();
    }

    Super::EndPlay(Reason);
}

void AAFCharacter::Tick(float Dt)
{
    Super::Tick(Dt);

    const float DesiredArmLength = bIsAiming ? AimCameraArmLength : NormalCameraArmLength;
    const float DesiredHeight = bIsAiming ? AimCameraHeight : NormalCameraHeight;
    const float SideSign = bLeftShoulder ? -1.f : 1.f;
    const FVector DesiredSocketOffset(0.f, SideSign * ShoulderOffsetY, DesiredHeight);

    CameraBoom->TargetArmLength = FMath::FInterpTo(
        CameraBoom->TargetArmLength,
        DesiredArmLength,
        Dt,
        CameraInterpSpeed);

    CameraBoom->SocketOffset = FMath::VInterpTo(
        CameraBoom->SocketOffset,
        DesiredSocketOffset,
        Dt,
        CameraInterpSpeed);

    FollowCamera->SetFieldOfView(FMath::FInterpTo(
        FollowCamera->FieldOfView,
        bIsAiming ? AimFOV : DefaultFOV,
        Dt,
        CameraInterpSpeed));

    if (bIsAiming && Controller)
    {
        const float RawPitch = FRotator::NormalizeAxis(
            Controller->GetControlRotation().Pitch - GetActorRotation().Pitch);
        AimPitch = FMath::Clamp(RawPitch, MinAimPitch, MaxAimPitch);
    }
    else
    {
        AimPitch = 0.f;
    }
}

void AAFCharacter::StartPrimaryFire()
{
    if (IsValid(EquippedWeapon) && !HealthComponent->IsDead())
    {
        EquippedWeapon->StartFire();
    }
}

void AAFCharacter::StopPrimaryFire()
{
    if (IsValid(EquippedWeapon))
    {
        EquippedWeapon->StopFire();
    }
}

void AAFCharacter::ReloadWeapon()
{
    if (IsValid(EquippedWeapon))
    {
        EquippedWeapon->Reload();
    }
}

void AAFCharacter::StartAiming()
{
    if (bIsAiming || !IsValid(EquippedWeapon) || HealthComponent->IsDead())
    {
        return;
    }

    bPreviousControllerYaw = bUseControllerRotationYaw;
    bPreviousOrientRotationToMovement = GetCharacterMovement()->bOrientRotationToMovement;

    bIsAiming = true;
    bUseControllerRotationYaw = true;
    GetCharacterMovement()->bOrientRotationToMovement = false;

    EquippedWeapon->SetAiming(true);
}

void AAFCharacter::StopAiming()
{
    if (!bIsAiming)
    {
        return;
    }

    bIsAiming = false;
    AimPitch = 0.f;

    bUseControllerRotationYaw = bPreviousControllerYaw;
    GetCharacterMovement()->bOrientRotationToMovement = bPreviousOrientRotationToMovement;

    if (IsValid(EquippedWeapon))
    {
        EquippedWeapon->SetAiming(false);
    }
}

void AAFCharacter::ToggleShoulder()
{
    bLeftShoulder = !bLeftShoulder;
    OnShoulderChanged(bLeftShoulder);
}

bool AAFCharacter::EquipWeapon(AAFWeaponBase* Weapon)
{
    if (!IsValid(Weapon) || HealthComponent->IsDead())
    {
        return false;
    }

    if (Weapon == EquippedWeapon)
    {
        return true;
    }

    if (!Weapon->bCanBePickedUp ||
        Weapon->GetOwner() ||
        FVector::DistSquared(GetActorLocation(), Weapon->GetActorLocation()) > FMath::Square(PickupDistance))
    {
        return false;
    }

    DropWeapon();

    EquippedWeapon = Weapon;
    Weapon->SetEquippedPawn(this);

    if (GetMesh()->DoesSocketExist(WeaponAttachSocket))
    {
        Weapon->AttachToComponent(
            GetMesh(),
            FAttachmentTransformRules::SnapToTargetNotIncludingScale,
            WeaponAttachSocket);
        Weapon->SetActorRelativeTransform(WeaponGripOffset);
    }
    else
    {
        Weapon->AttachToComponent(
            RootComponent,
            FAttachmentTransformRules::SnapToTargetNotIncludingScale);
        Weapon->SetActorRelativeLocation(FVector(25, 18, 40));
        Weapon->SetActorRelativeRotation(FRotator::ZeroRotator);
    }

    OnEquippedWeaponChanged(Weapon);
    return true;
}

void AAFCharacter::DropWeapon()
{
    StopAiming();

    if (!IsValid(EquippedWeapon))
    {
        EquippedWeapon = nullptr;
        return;
    }

    AAFWeaponBase* Dropped = EquippedWeapon;
    EquippedWeapon = nullptr;

    Dropped->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
    Dropped->SetEquippedPawn(nullptr);

    OnEquippedWeaponChanged(nullptr);
}

void AAFCharacter::HandleWeaponOwnerDeath()
{
    DropWeapon();
}
