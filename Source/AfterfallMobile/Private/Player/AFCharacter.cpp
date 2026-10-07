#include "Player/AFCharacter.h"

#include "Camera/CameraComponent.h"
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

AAFCharacter::AAFCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    DefaultWeaponClass = AAFHoundWeapon::StaticClass();

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
                + GetActorForwardVector().GetSafeNormal2D() * 180.0f;

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

    GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    GetCharacterMovement()->Velocity = FVector::ZeroVector;

    LaunchCharacter(
        HangingWallNormal.GetSafeNormal2D() * 140.0f + FVector(0.0f, 0.0f, -90.0f),
        true,
        true);

    HangingWallNormal = FVector::ZeroVector;
    HangingLedgeTop = FVector::ZeroVector;
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
            StartTraversalMove(
                EAFTraversalState::Vaulting,
                LandingLocation,
                TargetRotation,
                VaultDuration,
                FMath::Max(85.0f, ObstacleHeight + 45.0f));
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

    StartTraversalMove(
        EAFTraversalState::Mantling,
        MantleTarget,
        TargetRotation,
        MantleDuration,
        38.0f);

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
    float ArcHeight)
{
    if (!GetCharacterMovement())
    {
        return;
    }

    StopAiming();
    StopPrimaryFire();

    TraversalState = NewState;
    TraversalStartLocation = GetActorLocation();
    TraversalTargetLocation = TargetLocation;
    TraversalStartRotation = GetActorRotation();
    TraversalTargetRotation = TargetRotation;
    TraversalElapsed = 0.0f;
    TraversalDurationActive = FMath::Max(0.05f, Duration);
    TraversalArcHeight = FMath::Max(0.0f, ArcHeight);

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

    FVector Target =
        HangingLedgeTop
        - HangingWallNormal.GetSafeNormal2D() * (Radius + 28.0f);

    Target.Z =
        HangingLedgeTop.Z + HalfHeight + 2.0f;

    if (!CanOccupyCapsuleAt(Target))
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
        42.0f);
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

    if (GetCharacterMovement())
    {
        GetCharacterMovement()->GravityScale = 1.0f;
        GetCharacterMovement()->SetMovementMode(MOVE_Walking);
        GetCharacterMovement()->bOrientRotationToMovement = !bIsAiming;
    }

    bUseControllerRotationYaw = bIsAiming;

    HangingWallNormal = FVector::ZeroVector;
    HangingLedgeTop = FVector::ZeroVector;

    OnTraversalStateChanged(TraversalState);
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
