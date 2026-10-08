#include "Player/AFCharacter.h"

#include "Animation/AnimInstance.h"
#include "Animation/AnimSequenceBase.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Camera/CameraComponent.h"
#include "CollisionShape.h"
#include "Components/AFHealthComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Inventory/AFInventoryComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Weapons/AFHoundWeapon.h"
#include "World/AFTraversalTestCourse.h"
#include "TimerManager.h"

AAFCharacter::AAFCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    DefaultWeaponClass = AAFHoundWeapon::StaticClass();

    JumpStartAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Characters/Mannequins/Anims/Rifle/Jump/MM_Rifle_Jump_Start.MM_Rifle_Jump_Start")));
    JumpStartLoopAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Characters/Mannequins/Anims/Rifle/Jump/MM_Rifle_Jump_Start_Loop.MM_Rifle_Jump_Start_Loop")));
    JumpApexAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Characters/Mannequins/Anims/Rifle/Jump/MM_Rifle_Jump_Apex.MM_Rifle_Jump_Apex")));
    JumpFallLoopAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Characters/Mannequins/Anims/Rifle/Jump/MM_Rifle_Jump_Fall_Loop.MM_Rifle_Jump_Fall_Loop")));
    JumpLandAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Characters/Mannequins/Anims/Rifle/Jump/MM_Rifle_Jump_Fall_Land.MM_Rifle_Jump_Fall_Land")));

    // Retargeted Game Animation Sample assets exported to Manny.
    VaultRunAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Afterfall/Animations/Traversal_Retargeted/M_Neutral_Traversal_Vault_1_0_run_F_Lfoot.M_Neutral_Traversal_Vault_1_0_run_F_Lfoot")));
    VaultWalkAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Afterfall/Animations/Traversal_Retargeted/M_Neutral_Traversal_Vault_1_0_walk_F_Rfoot.M_Neutral_Traversal_Vault_1_0_walk_F_Rfoot")));
    HurdleRunAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Afterfall/Animations/Traversal_Retargeted/M_Neutral_Traversal_Hurdle_1_0_run_F_LFoot.M_Neutral_Traversal_Hurdle_1_0_run_F_LFoot")));
    MantleLowAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Afterfall/Animations/Traversal_Retargeted/M_Neutral_Traversal_Mantle_1_0_walk_F_Lfoot.M_Neutral_Traversal_Mantle_1_0_walk_F_Lfoot")));
    MantleMediumAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Afterfall/Animations/Traversal_Retargeted/M_Neutral_Traversal_Mantle_1_0_run_F_Rfoot.M_Neutral_Traversal_Mantle_1_0_run_F_Rfoot")));
    LedgeCatchAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Afterfall/Animations/Traversal_Retargeted/M_Neutral_Traversal_Catch_Mantle_high.M_Neutral_Traversal_Catch_Mantle_high")));
    LedgeClimbAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Afterfall/Animations/Traversal_Retargeted/M_Neutral_Traversal_Mantle_1_0_stand_F_Lfoot.M_Neutral_Traversal_Mantle_1_0_stand_F_Lfoot")));
    HighClimbAnimation = TSoftObjectPtr<UAnimSequenceBase>(
        FSoftObjectPath(TEXT("/Game/Afterfall/Animations/Traversal_Retargeted/M_Neutral_Traversal_Climb_Start_2_5_stand_F_Lfoot.M_Neutral_Traversal_Climb_Start_2_5_stand_F_Lfoot")));

    bUseControllerRotationPitch = false;
    bUseControllerRotationYaw = false;
    bUseControllerRotationRoll = false;

    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0.0f, 540.0f, 0.0f);
    GetCharacterMovement()->JumpZVelocity = 520.0f;
    GetCharacterMovement()->AirControl = 0.45f;

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

    PlayerInputComponent->BindAction(TEXT("Jump"), IE_Pressed, this, &AAFCharacter::TraversalJumpPressed);
    PlayerInputComponent->BindAction(TEXT("Jump"), IE_Released, this, &AAFCharacter::TraversalJumpReleased);
    PlayerInputComponent->BindAction(TEXT("DropLedge"), IE_Pressed, this, &AAFCharacter::DropFromLedge);
}

void AAFCharacter::MoveForward(float Value)
{
    MoveForwardInput = Value;

    if (TraversalState != EAFTraversalState::None)
    {
        if (TraversalState == EAFTraversalState::Hanging && Value < -0.55f)
        {
            DropFromLedge();
        }
        return;
    }

    if (Controller && !FMath::IsNearlyZero(Value))
    {
        const FRotator Rotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
        AddMovementInput(FRotationMatrix(Rotation).GetUnitAxis(EAxis::X), Value);
    }
}

void AAFCharacter::MoveRight(float Value)
{
    MoveRightInput = Value;

    if (TraversalState != EAFTraversalState::None)
    {
        return;
    }

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
    if (TraversalState == EAFTraversalState::None &&
        IsValid(EquippedWeapon) &&
        !HealthComponent->IsDead())
    {
        EquippedWeapon->TryFire();
    }
}

void AAFCharacter::BeginPlay()
{
    Super::BeginPlay();

    DefaultFOV = FollowCamera->FieldOfView;

    if (GetMesh())
    {
        SavedLocomotionAnimClass = GetMesh()->GetAnimClass();
    }

    CameraBoom->TargetArmLength = NormalCameraArmLength;
    CameraBoom->SocketOffset = FVector(
        0.f,
        bLeftShoulder ? -ShoulderOffsetY : ShoulderOffsetY,
        NormalCameraHeight);

    HealthComponent->OnDeath.AddDynamic(this, &AAFCharacter::HandleWeaponOwnerDeath);

#if WITH_EDITOR
    if (bAutoSpawnTraversalTestCourseInEditor && GetWorld())
    {
        bool bCourseExists = false;
        for (TActorIterator<AAFTraversalTestCourse> It(GetWorld()); It; ++It)
        {
            bCourseExists = true;
            break;
        }

        if (!bCourseExists)
        {
            const float HalfHeight = GetCapsuleComponent()
                ? GetCapsuleComponent()->GetScaledCapsuleHalfHeight()
                : 88.0f;

            const FVector CourseLocation =
                GetActorLocation()
                - FVector(0.0f, 0.0f, HalfHeight)
                + GetActorForwardVector().GetSafeNormal2D() * 80.0f;

            const FRotator CourseRotation(
                0.0f,
                GetActorRotation().Yaw,
                0.0f);

            GetWorld()->SpawnActor<AAFTraversalTestCourse>(
                AAFTraversalTestCourse::StaticClass(),
                CourseLocation,
                CourseRotation);
        }
    }
#endif

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

    bIsInAir =
        TraversalState == EAFTraversalState::None &&
        GetCharacterMovement() &&
        GetCharacterMovement()->IsFalling();
    VerticalVelocity = GetVelocity().Z;

    UpdateJumpVisual(Dt);

    if (TraversalState == EAFTraversalState::Vaulting ||
        TraversalState == EAFTraversalState::Mantling)
    {
        UpdateTraversal(Dt);
    }
    else if (TraversalState == EAFTraversalState::Hanging)
    {
        UpdateHanging(Dt);
    }
    else if (bAutoLedgeGrab &&
             GetCharacterMovement() &&
             GetCharacterMovement()->IsFalling())
    {
        LedgeGrabScanCooldown -= Dt;
        if (LedgeGrabScanCooldown <= 0.f)
        {
            LedgeGrabScanCooldown = 0.05f;
            TryAutoGrabLedge();
        }
    }
}


void AAFCharacter::Landed(const FHitResult& Hit)
{
    Super::Landed(Hit);

    bIsInAir = false;
    VerticalVelocity = 0.0f;

    if (TraversalState != EAFTraversalState::None || !bJumpVisualActive)
    {
        return;
    }

    SetJumpVisualPhase(EAFJumpVisualPhase::Landing);
}

void AAFCharacter::StartPrimaryFire()
{
    if (TraversalState == EAFTraversalState::None &&
        IsValid(EquippedWeapon) &&
        !HealthComponent->IsDead())
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
    if (TraversalState == EAFTraversalState::None && IsValid(EquippedWeapon))
    {
        EquippedWeapon->Reload();
    }
}

void AAFCharacter::StartAiming()
{
    if (TraversalState != EAFTraversalState::None ||
        bIsAiming ||
        !IsValid(EquippedWeapon) ||
        HealthComponent->IsDead())
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

void AAFCharacter::TraversalJumpPressed()
{
    if (!GetCharacterMovement())
    {
        return;
    }

    if (TraversalState == EAFTraversalState::Hanging)
    {
        ClimbFromLedge();
        return;
    }

    if (TraversalState != EAFTraversalState::None)
    {
        return;
    }

    if (GetCharacterMovement()->IsFalling())
    {
        TryAutoGrabLedge();
        return;
    }

    if (TryContextTraversal())
    {
        return;
    }

    bFallLoopVisualActive = false;
    JumpVisualPhase = EAFJumpVisualPhase::None;
    JumpVisualPhaseElapsed = 0.0f;
    SetJumpVisualPhase(EAFJumpVisualPhase::Start);
    Jump();
}

void AAFCharacter::TraversalJumpReleased()
{
    StopJumping();
}

void AAFCharacter::DropFromLedge()
{
    if (TraversalState != EAFTraversalState::Hanging || !GetCharacterMovement())
    {
        return;
    }

    TraversalState = EAFTraversalState::None;
    OnTraversalStateChanged(TraversalState);

    GetCharacterMovement()->GravityScale = 1.0f;
    GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->Velocity = FVector::ZeroVector;
    bUseControllerRotationYaw = false;

    LaunchCharacter(
        HangingWallNormal.GetSafeNormal2D() * 140.0f + FVector(0.0f, 0.0f, -90.0f),
        true,
        true);

    bFallLoopVisualActive = false;
    JumpVisualPhase = EAFJumpVisualPhase::None;
    JumpVisualPhaseElapsed = 0.0f;
    SetJumpVisualPhase(EAFJumpVisualPhase::Falling);

    HangingWallNormal = FVector::ZeroVector;
    HangingLedgeTop = FVector::ZeroVector;
    TraversalAlpha = 0.0f;
    SetTraversalWeaponStowed(false);
}

bool AAFCharacter::TryContextTraversal()
{
    if (TraversalState != EAFTraversalState::None ||
        !GetWorld() ||
        !GetCapsuleComponent() ||
        !GetCharacterMovement() ||
        GetCharacterMovement()->IsFalling())
    {
        return false;
    }

    FHitResult WallHit;
    FHitResult TopHit;
    float ObstacleHeight = 0.f;

    if (!FindObstacleTop(
            TraversalProbeDistance,
            WallHit,
            TopHit,
            ObstacleHeight))
    {
        return false;
    }

    if (ObstacleHeight < MinTraversalObstacleHeight ||
        ObstacleHeight > MantleMaxHeight)
    {
        return false;
    }

    FVector Forward = GetTraversalForward();
    if (Forward.IsNearlyZero())
    {
        Forward = GetActorForwardVector().GetSafeNormal2D();
    }

    FRotator TargetRotation = Forward.Rotation();
    TargetRotation.Pitch = 0.f;
    TargetRotation.Roll = 0.f;

    if (ObstacleHeight <= VaultMaxHeight)
    {
        FVector LandingLocation;
        if (FindVaultLanding(WallHit, LandingLocation))
        {
            const float HorizontalSpeed = GetVelocity().Size2D();
            TSoftObjectPtr<UAnimSequenceBase> VaultVisual =
                HorizontalSpeed >= HurdleSpeedThreshold
                    ? HurdleRunAnimation
                    : (HorizontalSpeed >= 140.0f
                        ? VaultRunAnimation
                        : VaultWalkAnimation);

            StartTraversalMove(
                EAFTraversalState::Vaulting,
                LandingLocation,
                TargetRotation,
                VaultDuration,
                FMath::Max(85.0f, ObstacleHeight + 45.0f),
                VaultVisual);
            return true;
        }
    }

    const float CapsuleRadius = GetCapsuleComponent()->GetScaledCapsuleRadius();
    const float CapsuleHalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();

    FVector MantleTarget = TopHit.ImpactPoint;
    MantleTarget -= WallHit.ImpactNormal.GetSafeNormal2D() * (CapsuleRadius * 0.45f);
    MantleTarget.Z = TopHit.ImpactPoint.Z + CapsuleHalfHeight + 2.0f;

    if (!CanOccupyCapsuleAt(MantleTarget))
    {
        return false;
    }

    TSoftObjectPtr<UAnimSequenceBase> MantleVisual;
    if (ObstacleHeight >= 165.0f)
    {
        MantleVisual = HighClimbAnimation;
    }
    else if (ObstacleHeight >= 115.0f || GetVelocity().Size2D() >= 220.0f)
    {
        MantleVisual = MantleMediumAnimation;
    }
    else
    {
        MantleVisual = MantleLowAnimation;
    }

    StartTraversalMove(
        EAFTraversalState::Mantling,
        MantleTarget,
        TargetRotation,
        MantleDuration,
        38.0f,
        MantleVisual);

    return true;
}

void AAFCharacter::UpdateTraversal(float DeltaSeconds)
{
    if (TraversalState != EAFTraversalState::Vaulting &&
        TraversalState != EAFTraversalState::Mantling)
    {
        return;
    }

    TraversalElapsed += FMath::Max(0.f, DeltaSeconds);

    const float Alpha = FMath::Clamp(
        TraversalElapsed / FMath::Max(0.01f, TraversalDurationActive),
        0.f,
        1.f);
    TraversalAlpha = Alpha;

    const FVector MidPoint =
        (TraversalStartLocation + TraversalTargetLocation) * 0.5f
        + FVector(0.0f, 0.0f, TraversalArcHeight);

    const float OneMinus = 1.0f - Alpha;
    const FVector NewLocation =
        OneMinus * OneMinus * TraversalStartLocation
        + 2.0f * OneMinus * Alpha * MidPoint
        + Alpha * Alpha * TraversalTargetLocation;

    const FRotator NewRotation = FMath::Lerp(
        TraversalStartRotation,
        TraversalTargetRotation,
        Alpha);

    SetActorLocationAndRotation(
        NewLocation,
        NewRotation,
        false,
        nullptr,
        ETeleportType::None);

    if (Alpha >= 1.0f - KINDA_SMALL_NUMBER)
    {
        FinishTraversalMove();
    }
}

void AAFCharacter::UpdateHanging(float DeltaSeconds)
{
    if (TraversalState != EAFTraversalState::Hanging ||
        !GetWorld() ||
        !GetCapsuleComponent())
    {
        return;
    }

    if (GetCharacterMovement())
    {
        GetCharacterMovement()->Velocity = FVector::ZeroVector;
    }

    if (FMath::Abs(MoveRightInput) < 0.1f)
    {
        return;
    }

    const FVector Right = GetActorRightVector().GetSafeNormal2D();
    const FVector Candidate =
        GetActorLocation()
        + Right * MoveRightInput * HangShimmySpeed * FMath::Max(0.f, DeltaSeconds);

    const float CapsuleRadius = GetCapsuleComponent()->GetScaledCapsuleRadius();

    FCollisionQueryParams Params(
        SCENE_QUERY_STAT(AFHangShimmy),
        false,
        this);
    Params.AddIgnoredActor(this);

    FHitResult WallHit;
    const FVector WallProbeStart =
        Candidate - HangingWallNormal * 4.0f;
    const FVector WallProbeEnd =
        Candidate - HangingWallNormal * (CapsuleRadius + 55.0f);

    if (!GetWorld()->LineTraceSingleByChannel(
            WallHit,
            WallProbeStart,
            WallProbeEnd,
            ECC_Visibility,
            Params))
    {
        return;
    }

    if (FMath::Abs(WallHit.ImpactNormal.Z) > 0.45f)
    {
        return;
    }

    FVector Adjusted = Candidate;
    const FVector HorizontalNormal = WallHit.ImpactNormal.GetSafeNormal2D();
    const FVector DesiredSurfacePoint =
        WallHit.ImpactPoint + HorizontalNormal * (CapsuleRadius + 3.0f);

    Adjusted.X = DesiredSurfacePoint.X;
    Adjusted.Y = DesiredSurfacePoint.Y;

    if (CanOccupyCapsuleAt(Adjusted))
    {
        HangingWallNormal = WallHit.ImpactNormal.GetSafeNormal();
        SetActorLocation(Adjusted, false);
    }
}

bool AAFCharacter::TryAutoGrabLedge()
{
    if (!bAutoLedgeGrab ||
        TraversalState != EAFTraversalState::None ||
        !GetWorld() ||
        !GetCapsuleComponent() ||
        !GetCharacterMovement() ||
        !GetCharacterMovement()->IsFalling())
    {
        return false;
    }

    // Require some forward commitment so merely falling beside scenery does
    // not make the character magnetically stick to every wall.
    if (MoveForwardInput < 0.10f)
    {
        return false;
    }

    const FVector Forward = GetTraversalForward();
    const FVector ActorLocation = GetActorLocation();

    FCollisionQueryParams Params(
        SCENE_QUERY_STAT(AFLedgeGrab),
        false,
        this);
    Params.AddIgnoredActor(this);

    FHitResult WallHit;
    const FVector WallStart =
        ActorLocation + FVector(0.0f, 0.0f, 28.0f);
    const FVector WallEnd =
        WallStart + Forward * FMath::Max(20.0f, LedgeGrabForwardDistance);

    if (!GetWorld()->LineTraceSingleByChannel(
            WallHit,
            WallStart,
            WallEnd,
            ECC_Visibility,
            Params))
    {
        return false;
    }

    if (FMath::Abs(WallHit.ImpactNormal.Z) > 0.45f)
    {
        return false;
    }

    const FVector TopProbeXY =
        WallHit.ImpactPoint - WallHit.ImpactNormal * 10.0f;

    FVector TopStart = TopProbeXY;
    TopStart.Z = ActorLocation.Z + LedgeTopMaxRelativeHeight + 45.0f;

    FVector TopEnd = TopProbeXY;
    TopEnd.Z = ActorLocation.Z + LedgeTopMinRelativeHeight - 35.0f;

    FHitResult TopHit;
    if (!GetWorld()->LineTraceSingleByChannel(
            TopHit,
            TopStart,
            TopEnd,
            ECC_Visibility,
            Params))
    {
        return false;
    }

    if (TopHit.ImpactNormal.Z < 0.60f)
    {
        return false;
    }

    const float RelativeTopHeight =
        TopHit.ImpactPoint.Z - ActorLocation.Z;

    if (RelativeTopHeight < LedgeTopMinRelativeHeight ||
        RelativeTopHeight > LedgeTopMaxRelativeHeight)
    {
        return false;
    }

    EnterLedgeHang(WallHit, TopHit);
    return TraversalState == EAFTraversalState::Hanging;
}

bool AAFCharacter::FindObstacleTop(
    float ForwardDistance,
    FHitResult& OutWallHit,
    FHitResult& OutTopHit,
    float& OutObstacleHeight) const
{
    if (!GetWorld() || !GetCapsuleComponent())
    {
        return false;
    }

    const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    const float FootZ = GetActorLocation().Z - HalfHeight;
    const FVector Forward = GetTraversalForward();

    FCollisionQueryParams Params(
        SCENE_QUERY_STAT(AFTraversalObstacle),
        false,
        this);
    Params.AddIgnoredActor(this);

    FVector WallStart = GetActorLocation();
    WallStart.Z = FootZ + 55.0f;

    const FVector WallEnd =
        WallStart + Forward * FMath::Max(40.0f, ForwardDistance);

    if (!GetWorld()->LineTraceSingleByChannel(
            OutWallHit,
            WallStart,
            WallEnd,
            ECC_Visibility,
            Params))
    {
        return false;
    }

    if (FMath::Abs(OutWallHit.ImpactNormal.Z) > 0.50f)
    {
        return false;
    }

    const FVector TopProbeXY =
        OutWallHit.ImpactPoint - OutWallHit.ImpactNormal * 10.0f;

    FVector TopStart = TopProbeXY;
    TopStart.Z = FootZ + MantleMaxHeight + 120.0f;

    FVector TopEnd = TopProbeXY;
    TopEnd.Z = FootZ - 25.0f;

    if (!GetWorld()->LineTraceSingleByChannel(
            OutTopHit,
            TopStart,
            TopEnd,
            ECC_Visibility,
            Params))
    {
        return false;
    }

    if (OutTopHit.ImpactNormal.Z < 0.58f)
    {
        return false;
    }

    OutObstacleHeight = OutTopHit.ImpactPoint.Z - FootZ;
    return OutObstacleHeight >= 0.0f;
}

bool AAFCharacter::FindVaultLanding(
    const FHitResult& WallHit,
    FVector& OutLandingLocation) const
{
    if (!GetWorld() || !GetCapsuleComponent())
    {
        return false;
    }

    const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    const float FootZ = GetActorLocation().Z - HalfHeight;
    const FVector Forward = GetTraversalForward();

    FCollisionQueryParams Params(
        SCENE_QUERY_STAT(AFVWithLanding),
        false,
        this);
    Params.AddIgnoredActor(this);

    for (int32 Attempt = 0; Attempt < 4; ++Attempt)
    {
        const float Extra = static_cast<float>(Attempt) * 55.0f;
        FVector CandidateXY =
            WallHit.ImpactPoint
            + Forward * (VaultLandingForwardDistance + Extra);

        FVector TraceStart = CandidateXY;
        TraceStart.Z = GetActorLocation().Z + MantleMaxHeight + 120.0f;

        FVector TraceEnd = CandidateXY;
        TraceEnd.Z = FootZ - 260.0f;

        FHitResult FloorHit;
        if (!GetWorld()->LineTraceSingleByChannel(
                FloorHit,
                TraceStart,
                TraceEnd,
                ECC_Visibility,
                Params))
        {
            continue;
        }

        if (FloorHit.ImpactNormal.Z < 0.62f)
        {
            continue;
        }

        FVector Candidate = FloorHit.ImpactPoint;
        Candidate.Z += HalfHeight + 2.0f;

        if (CanOccupyCapsuleAt(Candidate))
        {
            OutLandingLocation = Candidate;
            return true;
        }
    }

    return false;
}

bool AAFCharacter::CanOccupyCapsuleAt(const FVector& WorldLocation) const
{
    if (!GetWorld() || !GetCapsuleComponent())
    {
        return false;
    }

    const float Radius =
        GetCapsuleComponent()->GetScaledCapsuleRadius() * 0.96f;
    const float HalfHeight =
        GetCapsuleComponent()->GetScaledCapsuleHalfHeight() * 0.96f;

    FCollisionQueryParams Params(
        SCENE_QUERY_STAT(AFTraversalClearance),
        false,
        this);
    Params.AddIgnoredActor(this);

    return !GetWorld()->OverlapBlockingTestByChannel(
        WorldLocation,
        FQuat::Identity,
        ECC_Pawn,
        FCollisionShape::MakeCapsule(Radius, HalfHeight),
        Params);
}

void AAFCharacter::StartTraversalMove(
    EAFTraversalState NewState,
    const FVector& TargetLocation,
    const FRotator& TargetRotation,
    float Duration,
    float ArcHeight,
    TSoftObjectPtr<UAnimSequenceBase> VisualAnimation)
{
    if (!GetCharacterMovement())
    {
        return;
    }

    StopAiming();
    StopPrimaryFire();
    RestoreLocomotionAnimationBlueprint();
    SetTraversalWeaponStowed(true);

    TraversalState = NewState;
    TraversalStartLocation = GetActorLocation();
    TraversalTargetLocation = TargetLocation;
    TraversalStartRotation = GetActorRotation();
    TraversalTargetRotation = TargetRotation;
    TraversalElapsed = 0.0f;
    TraversalDurationActive =
        ResolveTraversalDuration(VisualAnimation, FMath::Max(0.05f, Duration));
    TraversalArcHeight = FMath::Max(0.0f, ArcHeight);

    if (!VisualAnimation.IsNull())
    {
        PlayFullBodySequence(VisualAnimation, false, TraversalVisualPlayRate);
    }

    GetCharacterMovement()->StopMovementImmediately();
    GetCharacterMovement()->SetMovementMode(MOVE_Flying);
    GetCharacterMovement()->GravityScale = 0.0f;
    GetCharacterMovement()->bOrientRotationToMovement = false;
    bUseControllerRotationYaw = false;

    OnTraversalStateChanged(TraversalState);
}

void AAFCharacter::EnterLedgeHang(
    const FHitResult& WallHit,
    const FHitResult& TopHit)
{
    if (!GetCapsuleComponent() || !GetCharacterMovement())
    {
        return;
    }

    const float CapsuleRadius =
        GetCapsuleComponent()->GetScaledCapsuleRadius();

    FVector HangLocation =
        WallHit.ImpactPoint
        + WallHit.ImpactNormal.GetSafeNormal2D() * (CapsuleRadius + 3.0f);

    HangLocation.Z =
        TopHit.ImpactPoint.Z - FMath::Max(10.0f, HangBodyDrop);

    if (!CanOccupyCapsuleAt(HangLocation))
    {
        return;
    }

    StopAiming();
    StopPrimaryFire();
    RestoreLocomotionAnimationBlueprint();
    SetTraversalWeaponStowed(true);

    HangingWallNormal = WallHit.ImpactNormal.GetSafeNormal();
    HangingLedgeTop = TopHit.ImpactPoint;

    TraversalState = EAFTraversalState::Hanging;

    GetCharacterMovement()->StopMovementImmediately();
    GetCharacterMovement()->SetMovementMode(MOVE_Flying);
    GetCharacterMovement()->GravityScale = 0.0f;
    GetCharacterMovement()->bOrientRotationToMovement = false;

    FVector FaceDirection = -HangingWallNormal;
    FaceDirection.Z = 0.0f;

    FRotator HangRotation = FaceDirection.Rotation();
    HangRotation.Pitch = 0.f;
    HangRotation.Roll = 0.f;

    SetActorLocationAndRotation(
        HangLocation,
        HangRotation,
        false,
        nullptr,
        ETeleportType::None);

    bUseControllerRotationYaw = false;

    if (!LedgeCatchAnimation.IsNull())
    {
        PlayFullBodySequence(
            LedgeCatchAnimation,
            false,
            TraversalVisualPlayRate);
    }

    OnTraversalStateChanged(TraversalState);
}

void AAFCharacter::ClimbFromLedge()
{
    if (TraversalState != EAFTraversalState::Hanging ||
        !GetCapsuleComponent())
    {
        return;
    }

    const float Radius =
        GetCapsuleComponent()->GetScaledCapsuleRadius();
    const float HalfHeight =
        GetCapsuleComponent()->GetScaledCapsuleHalfHeight();

    const FVector IntoLedge = -HangingWallNormal.GetSafeNormal2D();

    FVector Target = FVector::ZeroVector;
    bool bFoundClimbTarget = false;

    const float CandidateDepths[] =
    {
        Radius + 28.0f,
        Radius + 65.0f,
        Radius + 105.0f,
        Radius + 145.0f
    };

    for (const float Depth : CandidateDepths)
    {
        FVector Candidate =
            HangingLedgeTop + IntoLedge * Depth;
        Candidate.Z =
            HangingLedgeTop.Z + HalfHeight + 3.0f;

        if (CanOccupyCapsuleAt(Candidate))
        {
            Target = Candidate;
            bFoundClimbTarget = true;
            break;
        }
    }

    if (!bFoundClimbTarget)
    {
        return;
    }

    FVector Facing = -HangingWallNormal;
    Facing.Z = 0.0f;

    FRotator TargetRotation = Facing.Rotation();
    TargetRotation.Pitch = 0.f;
    TargetRotation.Roll = 0.f;

    StartTraversalMove(
        EAFTraversalState::Mantling,
        Target,
        TargetRotation,
        MantleDuration,
        42.0f,
        LedgeClimbAnimation);
}

void AAFCharacter::FinishTraversalMove()
{
    SetActorLocationAndRotation(
        TraversalTargetLocation,
        TraversalTargetRotation,
        false,
        nullptr,
        ETeleportType::None);

    TraversalState = EAFTraversalState::None;
    TraversalAlpha = 0.0f;

    if (GetCharacterMovement())
    {
        GetCharacterMovement()->GravityScale = 1.0f;
        GetCharacterMovement()->SetMovementMode(MOVE_Walking);
        GetCharacterMovement()->bOrientRotationToMovement = !bIsAiming;
    }

    bUseControllerRotationYaw = bIsAiming;

    HangingWallNormal = FVector::ZeroVector;
    HangingLedgeTop = FVector::ZeroVector;
    RestoreLocomotionAnimationBlueprint();
    SetTraversalWeaponStowed(false);

    OnTraversalStateChanged(TraversalState);
}


void AAFCharacter::SetJumpVisualPhase(EAFJumpVisualPhase NewPhase)
{
    if (JumpVisualPhase == NewPhase)
    {
        return;
    }

    JumpVisualPhase = NewPhase;
    JumpVisualPhaseElapsed = 0.0f;
    bFallLoopVisualActive = NewPhase == EAFJumpVisualPhase::Falling;

    switch (NewPhase)
    {
        case EAFJumpVisualPhase::Start:
        {
            UAnimSequenceBase* Sequence = JumpStartAnimation.LoadSynchronous();
            JumpStartVisualDuration = Sequence
                ? Sequence->GetPlayLength() / FMath::Max(0.1f, JumpVisualPlayRate)
                : 0.18f;

            if (!PlayFullBodySequence(JumpStartAnimation, false))
            {
                RestoreLocomotionAnimationBlueprint();
            }
            break;
        }

        case EAFJumpVisualPhase::RisingLoop:
            if (!PlayFullBodySequence(JumpStartLoopAnimation, true))
            {
                // If this specific loop is unavailable, hold the start pose only
                // briefly and let the apex/fall phases take over.
                PlayFullBodySequence(JumpStartAnimation, true);
            }
            break;

        case EAFJumpVisualPhase::Apex:
        {
            UAnimSequenceBase* Sequence = JumpApexAnimation.LoadSynchronous();
            JumpApexVisualDuration = Sequence
                ? Sequence->GetPlayLength() / FMath::Max(0.1f, JumpVisualPlayRate)
                : 0.12f;

            if (!PlayFullBodySequence(JumpApexAnimation, false))
            {
                SetJumpVisualPhase(EAFJumpVisualPhase::Falling);
            }
            break;
        }

        case EAFJumpVisualPhase::Falling:
            if (!PlayFullBodySequence(JumpFallLoopAnimation, true))
            {
                RestoreLocomotionAnimationBlueprint();
            }
            break;

        case EAFJumpVisualPhase::Landing:
        {
            UAnimSequenceBase* Sequence = JumpLandAnimation.LoadSynchronous();
            if (!Sequence || !PlayFullBodySequence(JumpLandAnimation, false))
            {
                RestoreLocomotionAnimationBlueprint();
                return;
            }

            const float Duration =
                Sequence->GetPlayLength() / FMath::Max(0.1f, JumpVisualPlayRate);

            GetWorldTimerManager().SetTimer(
                JumpVisualTimer,
                this,
                &AAFCharacter::RestoreLocomotionAnimationBlueprint,
                FMath::Max(0.10f, Duration * 0.92f),
                false);
            break;
        }

        case EAFJumpVisualPhase::None:
        default:
            RestoreLocomotionAnimationBlueprint();
            break;
    }
}

void AAFCharacter::UpdateJumpVisual(float DeltaSeconds)
{
    if (!bJumpVisualActive ||
        TraversalState != EAFTraversalState::None ||
        !GetCharacterMovement() ||
        !GetCharacterMovement()->IsFalling())
    {
        return;
    }

    JumpVisualPhaseElapsed += FMath::Max(0.0f, DeltaSeconds);

    switch (JumpVisualPhase)
    {
        case EAFJumpVisualPhase::Start:
            // The original bug was caused by letting this non-looping clip end
            // while the character was still rising. Move into the authored
            // rising loop before the start clip can freeze on its last frame.
            if (VerticalVelocity <= JumpApexVelocityThreshold)
            {
                SetJumpVisualPhase(EAFJumpVisualPhase::Apex);
            }
            else if (JumpVisualPhaseElapsed >=
                     FMath::Max(0.08f, JumpStartVisualDuration * 0.82f))
            {
                SetJumpVisualPhase(EAFJumpVisualPhase::RisingLoop);
            }
            break;

        case EAFJumpVisualPhase::RisingLoop:
            if (VerticalVelocity <= JumpApexVelocityThreshold)
            {
                SetJumpVisualPhase(EAFJumpVisualPhase::Apex);
            }
            break;

        case EAFJumpVisualPhase::Apex:
            if (VerticalVelocity < -JumpApexVelocityThreshold ||
                JumpVisualPhaseElapsed >=
                    FMath::Max(0.08f, JumpApexVisualDuration * 0.75f))
            {
                SetJumpVisualPhase(EAFJumpVisualPhase::Falling);
            }
            break;

        case EAFJumpVisualPhase::Falling:
        case EAFJumpVisualPhase::Landing:
        case EAFJumpVisualPhase::None:
        default:
            break;
    }
}

float AAFCharacter::ResolveTraversalDuration(
    TSoftObjectPtr<UAnimSequenceBase> Sequence,
    float FallbackDuration) const
{
    UAnimSequenceBase* LoadedSequence = Sequence.LoadSynchronous();
    if (!LoadedSequence)
    {
        return FMath::Max(0.05f, FallbackDuration);
    }

    return FMath::Max(
        0.05f,
        LoadedSequence->GetPlayLength() /
            FMath::Max(0.1f, TraversalVisualPlayRate));
}

bool AAFCharacter::PlayFullBodySequence(
    TSoftObjectPtr<UAnimSequenceBase> Sequence,
    bool bLoop,
    float PlayRate)
{
    if (!GetMesh())
    {
        return false;
    }

    UAnimSequenceBase* LoadedSequence = Sequence.LoadSynchronous();
    if (!LoadedSequence)
    {
        return false;
    }

    if (GetWorld())
    {
        GetWorldTimerManager().ClearTimer(JumpVisualTimer);
    }

    if (!SavedLocomotionAnimClass)
    {
        SavedLocomotionAnimClass = GetMesh()->GetAnimClass();
    }

    GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    GetMesh()->PlayAnimation(LoadedSequence, bLoop);

    if (UAnimSingleNodeInstance* SingleNode =
        GetMesh()->GetSingleNodeInstance())
    {
        const float ResolvedPlayRate =
            PlayRate > 0.0f ? PlayRate : JumpVisualPlayRate;
        SingleNode->SetPlayRate(FMath::Max(0.1f, ResolvedPlayRate));
    }

    bJumpVisualActive = true;
    return true;
}

void AAFCharacter::RestoreLocomotionAnimationBlueprint()
{
    if (GetWorld())
    {
        GetWorldTimerManager().ClearTimer(JumpVisualTimer);
    }

    if (GetMesh())
    {
        if (SavedLocomotionAnimClass)
        {
            GetMesh()->SetAnimInstanceClass(SavedLocomotionAnimClass);
        }
        else
        {
            GetMesh()->SetAnimationMode(EAnimationMode::AnimationBlueprint);
        }
    }

    bJumpVisualActive = false;
    bFallLoopVisualActive = false;
    JumpVisualPhase = EAFJumpVisualPhase::None;
    JumpVisualPhaseElapsed = 0.0f;
}

void AAFCharacter::SetTraversalWeaponStowed(bool bStowed)
{
    if (!bHideWeaponDuringTraversal || !IsValid(EquippedWeapon))
    {
        return;
    }

    EquippedWeapon->SetActorHiddenInGame(bStowed);
    EquippedWeapon->SetActorEnableCollision(!bStowed);
}

FVector AAFCharacter::GetTraversalForward() const
{
    if (Controller)
    {
        const FRotator ControlYaw(
            0.0f,
            Controller->GetControlRotation().Yaw,
            0.0f);

        return FRotationMatrix(ControlYaw)
            .GetUnitAxis(EAxis::X)
            .GetSafeNormal2D();
    }

    return GetActorForwardVector().GetSafeNormal2D();
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
