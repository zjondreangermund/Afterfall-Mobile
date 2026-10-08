#include "Player/AFCharacter.h"
#include "Player/AFTraversalPath.h"
#include "Animation/AnimSequence.h"

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

void AAFCharacter::CalcCamera(float DeltaTime, FMinimalViewInfo& OutResult)
{
    Super::CalcCamera(DeltaTime, OutResult);
    if (IsLocallyControlled() && GetMesh())
    {
        // Spring-arm collision must stay enabled. When a wall retracts the
        // camera into the body, hide the body only from its owning camera.
        const FVector Offset = OutResult.Location - GetActorLocation();
        const bool bInsideBody = Offset.SizeSquared2D() < FMath::Square(70.0f)
            && FMath::Abs(Offset.Z) < GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 30.0f;
        GetMesh()->SetOwnerNoSee(bSavedOwnerNoSee || bInsideBody);
    }
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
        bSavedOwnerNoSee = GetMesh()->bOwnerNoSee;
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

    if (bIsInAir && !bJumpVisualActive)
    {
        SetJumpVisualPhase(EAFJumpVisualPhase::Falling);
    }
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
            TryAutoGrabLedge();
            LedgeGrabScanCooldown = FMath::Max(LedgeGrabScanCooldown, 0.05f);
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
    GetWorldTimerManager().ClearTimer(TraversalPoseTimer);

    if (TraversalState != EAFTraversalState::Hanging || !GetCharacterMovement())
    {
        return;
    }

    const FVector AwayFromWall = HangingWallNormal.GetSafeNormal2D();
    EndTraversalMove(false);
    LaunchCharacter(AwayFromWall * 140.0f + FVector(0.0f, 0.0f, -90.0f), true, true);

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

    FRotator TargetRotation = (-WallHit.ImpactNormal.GetSafeNormal2D()).Rotation();
    TargetRotation.Pitch = 0.f;
    TargetRotation.Roll = 0.f;

    const float HorizontalSpeed = GetVelocity().Size2D();

    // The imported Game Animation Sample actions are authored around a
    // roughly 1 m obstacle. Keep low/fast hurdles separate from normal vaults
    // instead of treating every short wall as the same action.
    if (ObstacleHeight <= VaultMaxHeight)
    {
        FVector LandingLocation;
        if (FindVaultLanding(WallHit, TopHit, LandingLocation))
        {
            const bool bUseHurdle =
                ObstacleHeight <= HurdleMaxHeight &&
                HorizontalSpeed >= HurdleSpeedThreshold;

            TSoftObjectPtr<UAnimSequenceBase> VaultVisual;

            if (bUseHurdle)
            {
                VaultVisual = HurdleRunAnimation;
            }
            else if (HorizontalSpeed >= 185.0f)
            {
                VaultVisual = VaultRunAnimation;
            }
            else
            {
                VaultVisual = VaultWalkAnimation;
            }

            if (StartTraversalMove(
                EAFTraversalState::Vaulting,
                LandingLocation,
                TargetRotation,
                VaultDuration,
                VaultVisual,
                TopHit.ImpactPoint.Z))
            {
                return true;
            }
        }
    }

    // A tall wall should not instantly play a mantle from the ground.
    // Returning false lets TraversalJumpPressed perform a normal jump; the
    // airborne ledge scanner then enters Hanging when the hands reach the lip.
    if (ObstacleHeight > DirectMantleMaxHeight)
    {
        return false;
    }

    const float CapsuleRadius = GetCapsuleComponent()->GetScaledCapsuleRadius();
    const float CapsuleHalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();

    // Put the capsule clearly onto the top surface. The old target barely
    // crossed the wall edge, which made the body animation appear to climb
    // through or beside the obstacle.
    FVector MantleTarget = TopHit.ImpactPoint;
    MantleTarget -= WallHit.ImpactNormal.GetSafeNormal2D() * (CapsuleRadius + 24.0f);
    MantleTarget.Z = TopHit.ImpactPoint.Z + CapsuleHalfHeight + 3.0f;

    if (!CanOccupyCapsuleAt(MantleTarget))
    {
        return false;
    }

    // These Mantle_1_0 assets are approach variants (stand/walk/run), not
    // different wall heights. Select by approach speed; the actor path handles
    // the actual detected wall height.
    TSoftObjectPtr<UAnimSequenceBase> MantleVisual;
    if (HorizontalSpeed >= 230.0f)
    {
        MantleVisual = MantleMediumAnimation; // run variant
    }
    else if (HorizontalSpeed >= 70.0f)
    {
        MantleVisual = MantleLowAnimation; // walk variant
    }
    else
    {
        MantleVisual = LedgeClimbAnimation; // stand variant
    }

    return StartTraversalMove(
        EAFTraversalState::Mantling,
        MantleTarget,
        TargetRotation,
        MantleDuration,
        MantleVisual,
        TopHit.ImpactPoint.Z);
}

void AAFCharacter::UpdateTraversal(float DeltaSeconds)
{
    if (TraversalState != EAFTraversalState::Vaulting &&
        TraversalState != EAFTraversalState::Mantling)
    {
        return;
    }

    const float PreviousAlpha = TraversalAlpha;
    TraversalElapsed += FMath::Max(0.f, DeltaSeconds);

    const float Alpha = FMath::Clamp(
        TraversalElapsed / FMath::Max(0.01f, TraversalDurationActive),
        0.f,
        1.f);
    TraversalAlpha = Alpha;

    // Sweep every frame as well as checking the route before starting. Moving
    // props/ceilings can invalidate a previously clear traversal. Visit phase
    // boundaries on a slow frame instead of cutting diagonally through a wall.
    const float Steps[] = {0.35f, 0.75f, Alpha};
    for (float Step : Steps)
    {
        if (Step <= PreviousAlpha || Step > Alpha)
        {
            continue;
        }
        const FQuat NewRotation = FQuat::Slerp(
            TraversalStartRotation.Quaternion(), TraversalTargetRotation.Quaternion(),
            FMath::SmoothStep(0.0f, 1.0f, Step));
        FHitResult MoveHit;
        SetActorLocationAndRotation(EvaluateTraversalLocation(Step), NewRotation, true, &MoveHit);
        if (MoveHit.bBlockingHit || MoveHit.bStartPenetrating)
        {
            EndTraversalMove(false);
            return;
        }
    }

    if (Alpha >= 1.0f - KINDA_SMALL_NUMBER)
    {
        EndTraversalMove(true);
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
    Params.AddIgnoredActor(EquippedWeapon);

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

    // Recheck the lip at the new position. A wall continuing sideways does
    // not imply the ledge does, and climb-up must use the new ledge position.
    const FVector TopXY = WallHit.ImpactPoint - HorizontalNormal * 10.0f;
    FHitResult TopHit;
    if (!GetWorld()->LineTraceSingleByChannel(TopHit,
            FVector(TopXY.X, TopXY.Y, HangingLedgeTop.Z + 20.0f),
            FVector(TopXY.X, TopXY.Y, HangingLedgeTop.Z - 20.0f),
            ECC_Visibility, Params) ||
        !GetCharacterMovement()->IsWalkable(TopHit) ||
        FVector::DotProduct(HorizontalNormal, HangingWallNormal) < 0.9f)
    {
        return;
    }
    Adjusted.Z = TopHit.ImpactPoint.Z - FMath::Max(10.0f, HangBodyDrop);
    if (CanOccupyCapsuleAt(Adjusted) && CanMoveCapsuleBetween(GetActorLocation(), Adjusted))
    {
        HangingWallNormal = WallHit.ImpactNormal.GetSafeNormal();
        HangingLedgeTop = TopHit.ImpactPoint;
        FHitResult MoveHit;
        SetActorLocationAndRotation(Adjusted, (-HorizontalNormal).Rotation(), true, &MoveHit);
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

    if (LedgeGrabScanCooldown > 0.0f)
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
    Params.AddIgnoredActor(EquippedWeapon);

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
    Params.AddIgnoredActor(EquippedWeapon);

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
    const FHitResult& TopHit,
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
    Params.AddIgnoredActor(EquippedWeapon);

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

        // A broad platform is a mantle, not a vault landing. Do not vault
        // down an arbitrary drop or onto the next taller obstacle.
        if (!GetCharacterMovement()->IsWalkable(FloorHit) ||
            FloorHit.ImpactPoint.Z > TopHit.ImpactPoint.Z - 20.0f ||
            FMath::Abs(FloorHit.ImpactPoint.Z - FootZ) > 60.0f)
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
        GetCapsuleComponent()->GetScaledCapsuleRadius();
    const float HalfHeight =
        GetCapsuleComponent()->GetScaledCapsuleHalfHeight();

    FCollisionQueryParams Params(
        SCENE_QUERY_STAT(AFTraversalClearance),
        false,
        this);
    Params.AddIgnoredActor(this);
    Params.AddIgnoredActor(EquippedWeapon);

    return !GetWorld()->OverlapBlockingTestByChannel(
        WorldLocation,
        FQuat::Identity,
        GetCapsuleComponent()->GetCollisionObjectType(),
        FCollisionShape::MakeCapsule(Radius, HalfHeight),
        Params, FCollisionResponseParams(GetCapsuleComponent()->GetCollisionResponseToChannels()));
}

bool AAFCharacter::StartTraversalMove(
    EAFTraversalState NewState,
    const FVector& TargetLocation,
    const FRotator& TargetRotation,
    float Duration,
    TSoftObjectPtr<UAnimSequenceBase> VisualAnimation,
    float ObstacleTopZ)
{
    if (!GetCharacterMovement() || !GetCapsuleComponent() || !GetWorld())
    {
        return false;
    }

    TraversalStartLocation = GetActorLocation();
    TraversalTargetLocation = TargetLocation;
    TraversalClearanceZ = FMath::Max3(
        TraversalStartLocation.Z, TargetLocation.Z,
        ObstacleTopZ + GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 3.0f);
    if (!CanOccupyCapsuleAt(TargetLocation) || !IsTraversalPathClear())
    {
        return false;
    }
    SaveTraversalMovementSettings();

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
    TraversalAlpha = 0.0f;
    TraversalDurationActive =
        ResolveTraversalDuration(VisualAnimation, FMath::Max(0.05f, Duration));

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
    return true;
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

    if (!CanOccupyCapsuleAt(HangLocation) ||
        !CanMoveCapsuleBetween(GetActorLocation(), HangLocation))
    {
        return;
    }

    SaveTraversalMovementSettings();
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

    FHitResult HangMoveHit;
    SetActorLocationAndRotation(HangLocation, HangRotation, true, &HangMoveHit);
    if (HangMoveHit.bBlockingHit || HangMoveHit.bStartPenetrating)
    {
        EndTraversalMove(false);
        return;
    }

    bUseControllerRotationYaw = false;

    // Catch_Mantle_high actually ends in a ledge-contact pose, so it is a
    // much better persistent hang source than the 2.5 m climb-start clip.
    TSoftObjectPtr<UAnimSequenceBase> HangVisual =
        !LedgeCatchAnimation.IsNull()
            ? LedgeCatchAnimation
            : HighClimbAnimation;

    if (!HangVisual.IsNull() &&
        PlayFullBodySequence(
            HangVisual,
            false,
            TraversalVisualPlayRate))
    {
        if (UAnimSequenceBase* HangSequence = HangVisual.LoadSynchronous())
        {
            const float PauseDelay =
                (HangSequence->GetPlayLength() /
                    FMath::Max(0.1f, TraversalVisualPlayRate)) *
                FMath::Clamp(HangPoseFreezeFraction, 0.1f, 0.98f);

            GetWorldTimerManager().SetTimer(
                TraversalPoseTimer,
                this,
                &AAFCharacter::PauseTraversalVisualForHang,
                FMath::Max(0.05f, PauseDelay),
                false);
        }
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

        FCollisionQueryParams Params(SCENE_QUERY_STAT(AFClimbSupport), false, this);
        Params.AddIgnoredActor(EquippedWeapon);
        FHitResult Support;
        const FVector SurfacePoint(Candidate.X, Candidate.Y, HangingLedgeTop.Z);
        if (GetWorld()->LineTraceSingleByChannel(Support,
                SurfacePoint + FVector(0.f, 0.f, 15.f),
                SurfacePoint - FVector(0.f, 0.f, 15.f), ECC_Visibility, Params) &&
            GetCharacterMovement()->IsWalkable(Support) && CanOccupyCapsuleAt(Candidate))
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
        LedgeClimbAnimation,
        HangingLedgeTop.Z);
}

FVector AAFCharacter::EvaluateTraversalLocation(float Alpha) const
{
    const AFTraversalPath::Progress P = AFTraversalPath::Evaluate(Alpha);
    FVector Location = FMath::Lerp(TraversalStartLocation, TraversalTargetLocation, P.Forward);
    Location.Z = FMath::Lerp(TraversalStartLocation.Z, TraversalClearanceZ, P.Rise)
        + (TraversalTargetLocation.Z - TraversalClearanceZ) * P.Settle;
    return Location;
}

bool AAFCharacter::IsTraversalPathClear() const
{
    // Each phase is a straight segment, so these three sweeps cover the whole
    // path even if a frame hitch later skips one of the phase boundaries.
    const float PhaseEnds[] = {0.35f, 0.75f, 1.0f};
    FVector Previous = TraversalStartLocation;
    for (float Alpha : PhaseEnds)
    {
        const FVector Next = EvaluateTraversalLocation(Alpha);
        if (!CanMoveCapsuleBetween(Previous, Next))
        {
            return false;
        }
        Previous = Next;
    }
    return true;
}

bool AAFCharacter::CanMoveCapsuleBetween(const FVector& From, const FVector& To) const
{
    FCollisionQueryParams Params(SCENE_QUERY_STAT(AFTraversalPath), false, this);
    Params.AddIgnoredActor(EquippedWeapon);
    FHitResult Hit;
    return !GetWorld()->SweepSingleByChannel(Hit, From, To, FQuat::Identity,
        GetCapsuleComponent()->GetCollisionObjectType(),
        FCollisionShape::MakeCapsule(GetCapsuleComponent()->GetScaledCapsuleRadius(),
                                    GetCapsuleComponent()->GetScaledCapsuleHalfHeight()),
        Params, FCollisionResponseParams(GetCapsuleComponent()->GetCollisionResponseToChannels()));
}

void AAFCharacter::SaveTraversalMovementSettings()
{
    if (TraversalState == EAFTraversalState::None)
    {
        TraversalSavedGravity = GetCharacterMovement()->GravityScale;
        TraversalSavedOrientToMovement = bIsAiming
            ? bPreviousOrientRotationToMovement : GetCharacterMovement()->bOrientRotationToMovement;
        TraversalSavedControllerYaw = bIsAiming ? bPreviousControllerYaw : bUseControllerRotationYaw;
    }
}

void AAFCharacter::EndTraversalMove(bool bCompleted)
{
    GetWorldTimerManager().ClearTimer(TraversalPoseTimer);
    // Never teleport to a target after a blocked sweep.
    TraversalState = EAFTraversalState::None;
    TraversalAlpha = 0.0f;
    if (GetCharacterMovement())
    {
        GetCharacterMovement()->GravityScale = TraversalSavedGravity;
        GetCharacterMovement()->bOrientRotationToMovement = TraversalSavedOrientToMovement;
        GetCharacterMovement()->StopMovementImmediately();
        // Let movement find the actual floor, including after an interrupted climb.
        GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    }
    bUseControllerRotationYaw = TraversalSavedControllerYaw;
    HangingWallNormal = FVector::ZeroVector;
    HangingLedgeTop = FVector::ZeroVector;
    RestoreLocomotionAnimationBlueprint();
    SetTraversalWeaponStowed(false);
    LedgeGrabScanCooldown = bCompleted ? 0.2f : 0.5f;
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
        GetWorldTimerManager().ClearTimer(TraversalPoseTimer);
    }

    if (!SavedLocomotionAnimClass)
    {
        SavedLocomotionAnimClass = GetMesh()->GetAnimClass();
    }

    if (UAnimSequence* SourceSequence = Cast<UAnimSequence>(LoadedSequence))
    {
        // Keep source assets untouched: other characters/ABPs may need their root motion.
        TObjectPtr<UAnimSequence>& Playback = InPlaceSequences.FindOrAdd(SourceSequence);
        if (!Playback)
        {
            Playback = DuplicateObject<UAnimSequence>(SourceSequence, this);
            Playback->ClearFlags(RF_Public | RF_Standalone);
            Playback->SetFlags(RF_Transient);
            Playback->bEnableRootMotion = true;
            Playback->bForceRootLock = true;
            Playback->RootMotionRootLock = ERootMotionRootLock::AnimFirstFrame;
        }
        LoadedSequence = Playback;
    }

    GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    GetMesh()->PlayAnimation(LoadedSequence, bLoop);

    if (UAnimSingleNodeInstance* SingleNode =
        GetMesh()->GetSingleNodeInstance())
    {
        const float ResolvedPlayRate =
            PlayRate > 0.0f ? PlayRate : JumpVisualPlayRate;
        SingleNode->SetRootMotionMode(ERootMotionMode::IgnoreRootMotion);
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
        GetWorldTimerManager().ClearTimer(TraversalPoseTimer);
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

void AAFCharacter::PauseTraversalVisualForHang()
{
    if (TraversalState != EAFTraversalState::Hanging || !GetMesh())
    {
        return;
    }

    if (UAnimSingleNodeInstance* SingleNode =
        GetMesh()->GetSingleNodeInstance())
    {
        // Hold the authored grab pose instead of falling back to locomotion
        // while the character is attached to the ledge.
        if (UAnimSequenceBase* Sequence = Cast<UAnimSequenceBase>(SingleNode->GetCurrentAsset()))
        {
            SingleNode->SetPosition(Sequence->GetPlayLength() *
                FMath::Clamp(HangPoseFreezeFraction, 0.1f, 0.98f), false);
        }
        SingleNode->SetPlaying(false);
    }
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
