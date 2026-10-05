#include "Enemies/AFLeaperEnemy.h"

#include "AIController.h"
#include "Animation/AnimationAsset.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SphereComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Loot/AFLootPickup.h"
#include "Materials/MaterialInterface.h"
#include "NavigationSystem.h"
#include "TimerManager.h"

namespace AFLeaperWeakPoints
{
    static const FName Eye(TEXT("Eye"));
    static const FName FrontLeft(TEXT("FrontLeft"));
    static const FName FrontRight(TEXT("FrontRight"));
    static const FName RearLeft(TEXT("RearLeft"));
    static const FName RearRight(TEXT("RearRight"));
}

AAFLeaperEnemy::AAFLeaperEnemy()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
    PrimaryActorTick.TickGroup = TG_PostUpdateWork;

    EnemyId = TEXT("Leaper");
    WeakPointLootClass = AAFLootPickup::StaticClass();

    // Always give placed/spawned Leapers an AI controller so the native
    // predator state machine can patrol, freeze, investigate and attack.
    AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;
    AIControllerClass = AAIController::StaticClass();

    // Let weapon visibility traces reach the skeletal mesh / weak-point hitboxes
    // instead of being swallowed by the character capsule.
    GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
    GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    GetMesh()->SetCollisionResponseToAllChannels(ECR_Ignore);
    GetMesh()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    AddTickPrerequisiteComponent(GetMesh());

    WeakEyeHitbox = CreateDefaultSubobject<USphereComponent>(TEXT("WeakEyeHitbox"));
    ConfigureWeakPointHitbox(WeakEyeHitbox, TEXT("weak_eye"), 18.0f);

    WeakFrontLeftHitbox = CreateDefaultSubobject<USphereComponent>(TEXT("WeakFrontLeftHitbox"));
    ConfigureWeakPointHitbox(WeakFrontLeftHitbox, TEXT("weak_front_L"), 20.0f);

    WeakFrontRightHitbox = CreateDefaultSubobject<USphereComponent>(TEXT("WeakFrontRightHitbox"));
    ConfigureWeakPointHitbox(WeakFrontRightHitbox, TEXT("weak_front_R"), 20.0f);

    WeakRearLeftHitbox = CreateDefaultSubobject<USphereComponent>(TEXT("WeakRearLeftHitbox"));
    ConfigureWeakPointHitbox(WeakRearLeftHitbox, TEXT("weak_rear_L"), 18.0f);

    WeakRearRightHitbox = CreateDefaultSubobject<USphereComponent>(TEXT("WeakRearRightHitbox"));
    ConfigureWeakPointHitbox(WeakRearRightHitbox, TEXT("weak_rear_R"), 18.0f);

    auto AddWeakPoint = [this](
        FName Id,
        FName HitBone,
        FName CoverBone,
        FName MaterialSlot,
        float MaxHealth,
        float DamageMultiplier,
        FName LootItemId)
    {
        FAFLeaperWeakPointDefinition Definition;
        Definition.Id = Id;
        Definition.HitBone = HitBone;
        Definition.CoverBone = CoverBone;
        Definition.MaterialSlot = MaterialSlot;
        Definition.MaxHealth = MaxHealth;
        Definition.DamageMultiplier = DamageMultiplier;
        Definition.LootItemId = LootItemId;
        Definition.LootQuantity = 1;
        WeakPointDefinitions.Add(Definition);
    };

    AddWeakPoint(
        AFLeaperWeakPoints::Eye,
        TEXT("weak_eye"),
        TEXT("cover_eye"),
        TEXT("LEAP_WP_Eye_Grey"),
        45.0f,
        2.50f,
        TEXT("LeaperSensorPlate"));

    AddWeakPoint(
        AFLeaperWeakPoints::FrontLeft,
        TEXT("weak_front_L"),
        TEXT("cover_front_L"),
        TEXT("LEAP_WP_FrontL_Grey"),
        32.0f,
        2.00f,
        TEXT("LeaperActuatorPlate"));

    AddWeakPoint(
        AFLeaperWeakPoints::FrontRight,
        TEXT("weak_front_R"),
        TEXT("cover_front_R"),
        TEXT("LEAP_WP_FrontR_Grey"),
        32.0f,
        2.00f,
        TEXT("LeaperActuatorPlate"));

    AddWeakPoint(
        AFLeaperWeakPoints::RearLeft,
        TEXT("weak_rear_L"),
        TEXT("cover_rear_L"),
        TEXT("LEAP_WP_RearL_Grey"),
        28.0f,
        2.20f,
        TEXT("LeaperJumpActuator"));

    AddWeakPoint(
        AFLeaperWeakPoints::RearRight,
        TEXT("weak_rear_R"),
        TEXT("cover_rear_R"),
        TEXT("LEAP_WP_RearR_Grey"),
        28.0f,
        2.20f,
        TEXT("LeaperJumpActuator"));
}

void AAFLeaperEnemy::ConfigureWeakPointHitbox(
    USphereComponent* Hitbox,
    FName BoneName,
    float Radius)
{
    if (!Hitbox)
    {
        return;
    }

    Hitbox->SetupAttachment(GetMesh(), BoneName);
    Hitbox->SetSphereRadius(Radius);
    Hitbox->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Hitbox->SetCollisionObjectType(ECC_WorldDynamic);
    Hitbox->SetCollisionResponseToAllChannels(ECR_Ignore);
    Hitbox->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Hitbox->SetGenerateOverlapEvents(false);
    Hitbox->SetCanEverAffectNavigation(false);
}

void AAFLeaperEnemy::BeginPlay()
{
    Super::BeginPlay();

    InitializeWeakPoints();
    FindImportedHelperMaterials();
    SetAlertState(EAFLeaperAlertState::Scanning);

    if (GetMesh() && GetMesh()->GetBoneIndex(HeadBoneName) != INDEX_NONE)
    {
        HeadBaseLocalRotation = GetMesh()->GetBoneQuaternion(
            HeadBoneName,
            EBoneSpaces::LocalSpace).Rotator();
    }

    SightScanAccumulator = SightScanInterval;
    LastVisualTime = -1000000.0f;
    LastHeardTime = -1000000.0f;
    LastThreatTime = -1000000.0f;
    VisualLockStartTime = -1000000.0f;
    BodyTurnStartTime = -1000000.0f;
    NextPounceAllowedTime = 0.0f;

    if (!GetController())
    {
        SpawnDefaultController();
    }

    SetMovementSpeedForState();
    PlayStateAnimation();
}

void AAFLeaperEnemy::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    UpdateThreatSensing(DeltaSeconds);
    UpdateBehaviourMovement(DeltaSeconds);
    UpdateHeadTurn(DeltaSeconds);
}

void AAFLeaperEnemy::NotifyPlayerSeen(AActor* PlayerActor)
{
    if (!PlayerActor || PlayerActor == this || !GetWorld())
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();
    const bool bContinuousLock = VisualTarget.IsValid() &&
        VisualTarget.Get() == PlayerActor &&
        Now - LastVisualTime <= FMath::Max(0.20f, SightScanInterval * 2.5f);

    if (!bContinuousLock)
    {
        VisualLockStartTime = Now;
    }

    VisualTarget = PlayerActor;
    LastSeenLocation = PlayerActor->GetActorLocation();
    bHasLastSeenLocation = true;
    LastVisualTime = Now;
    LastThreatTime = Now;

    if (AlertState == EAFLeaperAlertState::Scanning)
    {
        SetAlertState(EAFLeaperAlertState::Alert);
    }
    else if (AlertState == EAFLeaperAlertState::Alert &&
             Now - VisualLockStartTime >= FMath::Max(0.0f, TargetConfirmationTime))
    {
        SetAlertState(EAFLeaperAlertState::Attacking);
    }
}

void AAFLeaperEnemy::NotifyGunshotHeard(
    FVector WorldLocation,
    float Loudness)
{
    if (!GetWorld())
    {
        return;
    }

    const float EffectiveRange = GunshotHearingRange *
        FMath::Clamp(Loudness, 0.25f, 4.0f);

    if (EffectiveRange <= 0.0f ||
        FVector::DistSquared(GetActorLocation(), WorldLocation) >
            FMath::Square(EffectiveRange))
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();
    LastHeardLocation = WorldLocation;
    LastHeardTime = Now;
    LastThreatTime = Now;
    bHasHeardLocation = true;

    if (AlertState == EAFLeaperAlertState::Scanning)
    {
        SetAlertState(EAFLeaperAlertState::Alert);
    }
}

void AAFLeaperEnemy::NotifyThreatSensed(
    FVector WorldLocation,
    EAFLeaperAlertState ThreatState)
{
    if (!GetWorld())
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();
    LastHeardLocation = WorldLocation;
    LastHeardTime = Now;
    LastThreatTime = Now;
    bHasHeardLocation = true;

    if (ThreatState != EAFLeaperAlertState::Scanning)
    {
        SetAlertState(ThreatState);
    }
}

void AAFLeaperEnemy::UpdateThreatSensing(float DeltaSeconds)
{
    if (!GetWorld())
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();

    if (bAutoSensePlayer)
    {
        SightScanAccumulator += FMath::Max(0.0f, DeltaSeconds);

        if (SightScanAccumulator >= FMath::Max(0.01f, SightScanInterval))
        {
            SightScanAccumulator = 0.0f;

            APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
            if (PlayerPawn && PlayerPawn != this)
            {
                const float DistanceSquared = FVector::DistSquared(
                    GetActorLocation(),
                    PlayerPawn->GetActorLocation());
                const bool bInsideSightRange = DistanceSquared <=
                    FMath::Square(PlayerSightRange);
                const bool bCloseEnoughToNoticeStillTarget = DistanceSquared <=
                    FMath::Square(CloseVisualDetectionRange);
                const bool bMovementDetected =
                    PlayerPawn->GetVelocity().Size2D() >= MovementDetectionSpeed;

                // White/search reacts primarily to movement. Once yellow/red,
                // keep checking the target even if the player freezes.
                const bool bShouldReactToVisiblePlayer =
                    AlertState != EAFLeaperAlertState::Scanning ||
                    bMovementDetected ||
                    bCloseEnoughToNoticeStillTarget;

                if (bInsideSightRange &&
                    bShouldReactToVisiblePlayer &&
                    HasLineOfSightToPlayer(PlayerPawn))
                {
                    NotifyPlayerSeen(PlayerPawn);
                }
            }
        }
    }

    if (VisualTarget.IsValid() &&
        Now - LastVisualTime > FMath::Max(0.0f, VisualMemoryDuration))
    {
        VisualTarget.Reset();
        VisualLockStartTime = -1000000.0f;

        if (AlertState == EAFLeaperAlertState::Attacking && !bPounceInProgress)
        {
            SetAlertState(EAFLeaperAlertState::Alert);
        }
    }

    if (bHasHeardLocation &&
        Now - LastHeardTime > FMath::Max(0.0f, HearingMemoryDuration))
    {
        bHasHeardLocation = false;
    }

    const bool bHasRecentVisual = VisualTarget.IsValid();
    const bool bHasRecentHearing = bHasHeardLocation;
    if (AlertState == EAFLeaperAlertState::Alert &&
        !bHasRecentVisual &&
        !bHasRecentHearing &&
        Now - LastThreatTime > FMath::Max(0.0f, AlertMemoryDuration))
    {
        SetAlertState(EAFLeaperAlertState::Scanning);
    }
}

bool AAFLeaperEnemy::HasLineOfSightToPlayer(AActor* PlayerActor) const
{
    if (!GetWorld() || !PlayerActor)
    {
        return false;
    }

    const FVector EyeLocation = GetHeadWorldLocation();
    const FVector TargetLocation = PlayerActor->GetActorLocation() +
        FVector(0.0f, 0.0f, 80.0f);

    FCollisionQueryParams QueryParams(
        SCENE_QUERY_STAT(AFLeaperSight),
        true,
        this);
    QueryParams.AddIgnoredActor(this);

    FHitResult Hit;
    if (!GetWorld()->LineTraceSingleByChannel(
            Hit,
            EyeLocation,
            TargetLocation,
            ECC_Visibility,
            QueryParams))
    {
        return true;
    }

    return Hit.GetActor() == PlayerActor;
}

FVector AAFLeaperEnemy::GetHeadWorldLocation() const
{
    if (GetMesh() && GetMesh()->GetBoneIndex(HeadBoneName) != INDEX_NONE)
    {
        return GetMesh()->GetBoneLocation(HeadBoneName);
    }

    return GetActorLocation() + FVector(0.0f, 0.0f, 100.0f);
}

void AAFLeaperEnemy::UpdateHeadTurn(float DeltaSeconds)
{
    if (!GetMesh() ||
        GetMesh()->GetBoneIndex(HeadBoneName) == INDEX_NONE ||
        !GetWorld())
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();
    const bool bTrackingVisual = VisualTarget.IsValid() &&
        Now - LastVisualTime <= FMath::Max(0.0f, VisualMemoryDuration);
    const bool bTrackingHearing = bHasHeardLocation &&
        Now - LastHeardTime <= FMath::Max(0.0f, HearingMemoryDuration);

    float DesiredYaw = 0.0f;
    float DesiredPitch = 0.0f;

    if ((bTrackingVisual && VisualTarget.IsValid()) || bTrackingHearing)
    {
        FVector LookTarget = LastHeardLocation;
        if (bTrackingVisual && VisualTarget.IsValid())
        {
            LookTarget = VisualTarget->GetActorLocation() + FVector(0.0f, 0.0f, 80.0f);
        }

        const FVector LocalDirection = GetActorTransform().InverseTransformVectorNoScale(
            LookTarget - GetHeadWorldLocation());
        const float HorizontalLength = FMath::Max(
            1.0f,
            FVector(LocalDirection.X, LocalDirection.Y, 0.0f).Size());

        DesiredYaw = FMath::Clamp(
            FMath::RadiansToDegrees(FMath::Atan2(LocalDirection.Y, LocalDirection.X)),
            -MaxHeadYaw,
            MaxHeadYaw);
        DesiredPitch = FMath::Clamp(
            FMath::RadiansToDegrees(FMath::Atan2(LocalDirection.Z, HorizontalLength)),
            -MaxHeadPitch,
            MaxHeadPitch);
    }
    else
    {
        // Independent predator scan. Two unequal waves prevent a robotic
        // left-right metronome and keep the head alive while the body crawls.
        ScanClock += FMath::Max(0.0f, DeltaSeconds) * ScanningHeadSpeed;
        const float Primary = FMath::Sin(ScanClock * 1.17f);
        const float Secondary = FMath::Sin(ScanClock * 0.43f + 1.15f);
        const float Vertical = FMath::Sin(ScanClock * 0.71f + 0.60f);
        DesiredYaw = FMath::Clamp(
            ScanningHeadYaw * ((Primary * 0.78f) + (Secondary * 0.22f)),
            -MaxHeadYaw,
            MaxHeadYaw);
        DesiredPitch = FMath::Clamp(
            ScanningHeadPitch * Vertical,
            -MaxHeadPitch,
            MaxHeadPitch);
    }

    const float TurnSpeed = (bTrackingVisual || bTrackingHearing)
        ? ThreatHeadTurnSpeed
        : HeadTurnSpeed;
    CurrentHeadYaw = FMath::FInterpTo(
        CurrentHeadYaw,
        DesiredYaw,
        FMath::Max(0.0f, DeltaSeconds),
        TurnSpeed);
    CurrentHeadPitch = FMath::FInterpTo(
        CurrentHeadPitch,
        DesiredPitch,
        FMath::Max(0.0f, DeltaSeconds),
        TurnSpeed);

    const FRotator HeadOffset(
        CurrentHeadPitch * HeadPitchSign,
        CurrentHeadYaw * HeadYawSign,
        0.0f);
    GetMesh()->SetBoneRotationByName(
        HeadBoneName,
        HeadBaseLocalRotation + HeadOffset,
        EBoneSpaces::LocalSpace);
}

void AAFLeaperEnemy::InitializeWeakPoints()
{
    WeakPointStates.Reset();

    for (const FAFLeaperWeakPointDefinition& Definition : WeakPointDefinitions)
    {
        if (Definition.Id.IsNone())
        {
            continue;
        }

        FAFLeaperWeakPointState State;
        State.MaxHealth = FMath::Max(1.0f, Definition.MaxHealth);
        State.CurrentHealth = State.MaxHealth;
        State.bDiscovered = false;
        State.bBroken = false;
        WeakPointStates.Add(Definition.Id, State);
    }
}

void AAFLeaperEnemy::FindImportedHelperMaterials()
{
    if (!GetMesh())
    {
        return;
    }

    for (int32 Index = 0; Index < GetMesh()->GetNumMaterials(); ++Index)
    {
        UMaterialInterface* Material = GetMesh()->GetMaterial(Index);
        if (!Material)
        {
            continue;
        }

        const FString MaterialName = Material->GetName();

        if (!DiscoveredWeakPointMaterial &&
            MaterialName.Contains(TEXT("LEAP_WP_Discovered_PaleYellow")))
        {
            DiscoveredWeakPointMaterial = Material;
        }

        if (!HitFlashWeakPointMaterial &&
            MaterialName.Contains(TEXT("LEAP_WP_Hit_WhiteYellow")))
        {
            HitFlashWeakPointMaterial = Material;
        }

        if (!ScanningSignalMaterial &&
            MaterialName.Contains(TEXT("LEAP_SIGNAL_Scan_White")))
        {
            ScanningSignalMaterial = Material;
        }

        if (!AlertSignalMaterial &&
            MaterialName.Contains(TEXT("LEAP_SIGNAL_Alert_Yellow")))
        {
            AlertSignalMaterial = Material;
        }

        if (!AttackSignalMaterial &&
            MaterialName.Contains(TEXT("LEAP_SIGNAL_Attack_Red")))
        {
            AttackSignalMaterial = Material;
        }
    }
}

void AAFLeaperEnemy::SetAlertState(EAFLeaperAlertState NewState)
{
    if (AlertState == NewState)
    {
        ApplyAlertMaterial();
        return;
    }

    AlertState = NewState;
    ApplyAlertMaterial();
    SetMovementSpeedForState();

    const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
    if (AlertState == EAFLeaperAlertState::Scanning)
    {
        NextPatrolRetargetTime = 0.0f;
    }
    else if (AlertState == EAFLeaperAlertState::Alert)
    {
        // Freeze immediately. The head turns first, then the body follows.
        StopAIMovement();
        BodyTurnStartTime = Now + FMath::Max(0.0f, AlertBodyTurnDelay);
    }

    PlayStateAnimation();
    OnAlertStateChanged.Broadcast(AlertState);
}

void AAFLeaperEnemy::ApplyAlertMaterial()
{
    if (!GetMesh() || SignalMaterialSlot.IsNone())
    {
        return;
    }

    const int32 MaterialIndex = GetMesh()->GetMaterialIndex(SignalMaterialSlot);
    if (MaterialIndex == INDEX_NONE)
    {
        return;
    }

    UMaterialInterface* DesiredMaterial = nullptr;

    switch (AlertState)
    {
        case EAFLeaperAlertState::Scanning:
            DesiredMaterial = ScanningSignalMaterial;
            break;

        case EAFLeaperAlertState::Alert:
            DesiredMaterial = AlertSignalMaterial;
            break;

        case EAFLeaperAlertState::Attacking:
            DesiredMaterial = AttackSignalMaterial;
            break;

        default:
            break;
    }

    if (DesiredMaterial)
    {
        GetMesh()->SetMaterial(MaterialIndex, DesiredMaterial);
    }
}

float AAFLeaperEnemy::TakeDamage(
    float DamageAmount,
    FDamageEvent const& DamageEvent,
    AController* EventInstigator,
    AActor* DamageCauser)
{
    float FinalDamage = DamageAmount;

    // A hit is also a close-range threat report. Projectile and hitscan
    // weapons can therefore make the Leaper snap toward the impact without
    // requiring every weapon Blueprint to know about this enemy class.
    FVector ThreatLocation = GetActorLocation();
    if (DamageCauser)
    {
        ThreatLocation = DamageCauser->GetActorLocation();
    }

    if (DamageAmount > 0.0f && DamageEvent.IsOfType(FPointDamageEvent::ClassID))
    {
        const FPointDamageEvent& PointEvent =
            static_cast<const FPointDamageEvent&>(DamageEvent);

        ThreatLocation = PointEvent.HitInfo.ImpactPoint;

        const FName WeakPointId = ResolveWeakPointId(PointEvent.HitInfo);

        if (!WeakPointId.IsNone())
        {
            const FAFLeaperWeakPointDefinition* Definition =
                FindWeakPointDefinition(WeakPointId);

            const bool bAcceptedWeakPointDamage = ApplyWeakPointDamage(
                WeakPointId,
                DamageAmount,
                PointEvent.HitInfo.ImpactPoint);

            if (Definition && bAcceptedWeakPointDamage)
            {
                FinalDamage *= FMath::Max(1.0f, Definition->DamageMultiplier);
            }
        }
    }

    if (DamageAmount > 0.0f)
    {
        NotifyGunshotHeard(ThreatLocation, 1.0f);
    }

    if (FinalDamage > 0.0f && AlertState == EAFLeaperAlertState::Scanning)
    {
        SetAlertState(EAFLeaperAlertState::Alert);
    }

    return Super::TakeDamage(
        FinalDamage,
        DamageEvent,
        EventInstigator,
        DamageCauser);
}

FName AAFLeaperEnemy::ResolveWeakPointId(const FHitResult& HitInfo) const
{
    const UPrimitiveComponent* HitComponent = HitInfo.GetComponent();

    if (HitComponent == WeakEyeHitbox)
    {
        return AFLeaperWeakPoints::Eye;
    }

    if (HitComponent == WeakFrontLeftHitbox)
    {
        return AFLeaperWeakPoints::FrontLeft;
    }

    if (HitComponent == WeakFrontRightHitbox)
    {
        return AFLeaperWeakPoints::FrontRight;
    }

    if (HitComponent == WeakRearLeftHitbox)
    {
        return AFLeaperWeakPoints::RearLeft;
    }

    if (HitComponent == WeakRearRightHitbox)
    {
        return AFLeaperWeakPoints::RearRight;
    }

    if (!HitInfo.BoneName.IsNone())
    {
        const FString HitBoneString = HitInfo.BoneName.ToString();

        for (const FAFLeaperWeakPointDefinition& Definition : WeakPointDefinitions)
        {
            if ((!Definition.HitBone.IsNone() &&
                 (HitInfo.BoneName == Definition.HitBone ||
                  HitBoneString.StartsWith(Definition.HitBone.ToString()))) ||
                (!Definition.CoverBone.IsNone() &&
                 (HitInfo.BoneName == Definition.CoverBone ||
                  HitBoneString.StartsWith(Definition.CoverBone.ToString()))))
            {
                return Definition.Id;
            }
        }
    }

    return NAME_None;
}

const FAFLeaperWeakPointDefinition* AAFLeaperEnemy::FindWeakPointDefinition(
    FName WeakPointId) const
{
    return WeakPointDefinitions.FindByPredicate(
        [WeakPointId](const FAFLeaperWeakPointDefinition& Definition)
        {
            return Definition.Id == WeakPointId;
        });
}

USphereComponent* AAFLeaperEnemy::FindWeakPointHitbox(FName WeakPointId) const
{
    if (WeakPointId == AFLeaperWeakPoints::Eye)
    {
        return WeakEyeHitbox;
    }

    if (WeakPointId == AFLeaperWeakPoints::FrontLeft)
    {
        return WeakFrontLeftHitbox;
    }

    if (WeakPointId == AFLeaperWeakPoints::FrontRight)
    {
        return WeakFrontRightHitbox;
    }

    if (WeakPointId == AFLeaperWeakPoints::RearLeft)
    {
        return WeakRearLeftHitbox;
    }

    if (WeakPointId == AFLeaperWeakPoints::RearRight)
    {
        return WeakRearRightHitbox;
    }

    return nullptr;
}

bool AAFLeaperEnemy::ApplyWeakPointDamage(
    FName WeakPointId,
    float DamageAmount,
    FVector HitLocation)
{
    if (DamageAmount <= 0.0f)
    {
        return false;
    }

    FAFLeaperWeakPointState* State = WeakPointStates.Find(WeakPointId);
    if (!State || State->bBroken)
    {
        return false;
    }

    if (!State->bDiscovered)
    {
        State->bDiscovered = true;
        SetWeakPointMaterial(WeakPointId, DiscoveredWeakPointMaterial);
        OnWeakPointDiscovered.Broadcast(WeakPointId);
    }

    State->CurrentHealth = FMath::Clamp(
        State->CurrentHealth - DamageAmount,
        0.0f,
        State->MaxHealth);

    const float NormalizedHealth =
        State->MaxHealth > 0.0f
            ? State->CurrentHealth / State->MaxHealth
            : 0.0f;

    BeginWeakPointFlash(WeakPointId);
    OnWeakPointHit.Broadcast(WeakPointId, NormalizedHealth);

    if (State->CurrentHealth <= 0.0f)
    {
        BreakWeakPoint(WeakPointId, HitLocation);
    }

    return true;
}

bool AAFLeaperEnemy::IsWeakPointDiscovered(FName WeakPointId) const
{
    const FAFLeaperWeakPointState* State = WeakPointStates.Find(WeakPointId);
    return State && State->bDiscovered;
}

bool AAFLeaperEnemy::IsWeakPointBroken(FName WeakPointId) const
{
    const FAFLeaperWeakPointState* State = WeakPointStates.Find(WeakPointId);
    return State && State->bBroken;
}

bool AAFLeaperEnemy::GetWeakPointState(
    FName WeakPointId,
    FAFLeaperWeakPointState& OutState) const
{
    const FAFLeaperWeakPointState* State = WeakPointStates.Find(WeakPointId);
    if (!State)
    {
        return false;
    }

    OutState = *State;
    return true;
}

void AAFLeaperEnemy::SetWeakPointMaterial(
    FName WeakPointId,
    UMaterialInterface* Material)
{
    if (!Material || !GetMesh())
    {
        return;
    }

    const FAFLeaperWeakPointDefinition* Definition =
        FindWeakPointDefinition(WeakPointId);

    if (!Definition || Definition->MaterialSlot.IsNone())
    {
        return;
    }

    const int32 MaterialIndex =
        GetMesh()->GetMaterialIndex(Definition->MaterialSlot);

    if (MaterialIndex != INDEX_NONE)
    {
        GetMesh()->SetMaterial(MaterialIndex, Material);
    }
}

void AAFLeaperEnemy::BeginWeakPointFlash(FName WeakPointId)
{
    if (!HitFlashWeakPointMaterial || !GetWorld())
    {
        return;
    }

    SetWeakPointMaterial(WeakPointId, HitFlashWeakPointMaterial);

    FTimerHandle& Handle = WeakPointFlashTimers.FindOrAdd(WeakPointId);

    FTimerDelegate TimerDelegate;
    TimerDelegate.BindUObject(
        this,
        &AAFLeaperEnemy::EndWeakPointFlash,
        WeakPointId);

    GetWorldTimerManager().SetTimer(
        Handle,
        TimerDelegate,
        WeakPointHitFlashDuration,
        false);
}

void AAFLeaperEnemy::EndWeakPointFlash(FName WeakPointId)
{
    const FAFLeaperWeakPointState* State = WeakPointStates.Find(WeakPointId);
    if (!State || State->bBroken)
    {
        return;
    }

    if (State->bDiscovered)
    {
        SetWeakPointMaterial(WeakPointId, DiscoveredWeakPointMaterial);
    }
}

void AAFLeaperEnemy::BreakWeakPoint(
    FName WeakPointId,
    FVector HitLocation)
{
    FAFLeaperWeakPointState* State = WeakPointStates.Find(WeakPointId);
    const FAFLeaperWeakPointDefinition* Definition =
        FindWeakPointDefinition(WeakPointId);

    if (!State || !Definition || State->bBroken)
    {
        return;
    }

    State->bBroken = true;
    State->CurrentHealth = 0.0f;

    if (GetWorld())
    {
        if (FTimerHandle* ExistingHandle = WeakPointFlashTimers.Find(WeakPointId))
        {
            GetWorldTimerManager().ClearTimer(*ExistingHandle);
        }
    }

    if (GetMesh() &&
        !Definition->CoverBone.IsNone() &&
        GetMesh()->GetBoneIndex(Definition->CoverBone) != INDEX_NONE)
    {
        GetMesh()->HideBoneByName(
            Definition->CoverBone,
            EPhysBodyOp::PBO_None);
    }

    if (USphereComponent* Hitbox = FindWeakPointHitbox(WeakPointId))
    {
        Hitbox->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }

    FVector BreakLocation = HitLocation;

    if (GetMesh() &&
        !Definition->HitBone.IsNone() &&
        GetMesh()->GetBoneIndex(Definition->HitBone) != INDEX_NONE)
    {
        BreakLocation = GetMesh()->GetBoneLocation(Definition->HitBone);
    }

    SpawnWeakPointLoot(*Definition, BreakLocation);
    OnWeakPointBroken.Broadcast(WeakPointId, BreakLocation);
}

void AAFLeaperEnemy::SpawnWeakPointLoot(
    const FAFLeaperWeakPointDefinition& Definition,
    FVector HitLocation)
{
    if (!GetWorld() || !WeakPointLootClass)
    {
        return;
    }

    FActorSpawnParameters SpawnParameters;
    SpawnParameters.Owner = this;
    SpawnParameters.Instigator = this;
    SpawnParameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;

    AAFLootPickup* Loot = GetWorld()->SpawnActor<AAFLootPickup>(
        WeakPointLootClass,
        HitLocation,
        GetActorRotation(),
        SpawnParameters);

    if (!Loot)
    {
        return;
    }

    Loot->ConfigureLoot(
        Definition.LootItemId,
        Definition.LootQuantity);

    FVector AwayFromBody = HitLocation - GetActorLocation();
    AwayFromBody.Z = FMath::Max(AwayFromBody.Z, 80.0f);

    if (!AwayFromBody.Normalize())
    {
        AwayFromBody = FVector::UpVector;
    }

    Loot->DropWithImpulse(
        AwayFromBody * 260.0f + FVector(0.0f, 0.0f, 180.0f));
}

void AAFLeaperEnemy::StopAIMovement()
{
    if (AAIController* AI = Cast<AAIController>(GetController()))
    {
        AI->StopMovement();
    }
    GetCharacterMovement()->StopMovementImmediately();
}

void AAFLeaperEnemy::SetMovementSpeedForState()
{
    if (!GetCharacterMovement())
    {
        return;
    }

    GetCharacterMovement()->MaxWalkSpeed =
        AlertState == EAFLeaperAlertState::Attacking
            ? AttackMoveSpeed
            : ScanningMoveSpeed;
}

void AAFLeaperEnemy::PlayStateAnimation()
{
    if (!GetMesh())
    {
        return;
    }

    UAnimationAsset* DesiredAnimation = nullptr;
    bool bLoop = true;

    switch (AlertState)
    {
        case EAFLeaperAlertState::Scanning:
            DesiredAnimation = CrawlAnimation;
            break;

        case EAFLeaperAlertState::Alert:
            DesiredAnimation = AlertStanceAnimation;
            break;

        case EAFLeaperAlertState::Attacking:
            DesiredAnimation = AttackCrawlAnimation ? AttackCrawlAnimation : CrawlAnimation;
            break;

        default:
            break;
    }

    if (DesiredAnimation)
    {
        GetMesh()->PlayAnimation(DesiredAnimation, bLoop);
    }
}

bool AAFLeaperEnemy::GetCurrentThreatLocation(FVector& OutLocation) const
{
    if (VisualTarget.IsValid())
    {
        OutLocation = VisualTarget->GetActorLocation();
        return true;
    }

    if (bHasHeardLocation)
    {
        OutLocation = LastHeardLocation;
        return true;
    }

    if (bHasLastSeenLocation)
    {
        OutLocation = LastSeenLocation;
        return true;
    }

    return false;
}

void AAFLeaperEnemy::UpdateScanningPatrol()
{
    if (!GetWorld())
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();
    if (Now < NextPatrolRetargetTime)
    {
        return;
    }

    NextPatrolRetargetTime = Now + FMath::FRandRange(
        FMath::Min(PatrolRetargetMin, PatrolRetargetMax),
        FMath::Max(PatrolRetargetMin, PatrolRetargetMax));

    AAIController* AI = Cast<AAIController>(GetController());
    UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
    if (!AI || !Nav)
    {
        return;
    }

    FNavLocation PatrolPoint;
    if (Nav->GetRandomReachablePointInRadius(
            GetActorLocation(),
            FMath::Max(100.0f, PatrolRadius),
            PatrolPoint))
    {
        AI->MoveToLocation(
            PatrolPoint.Location,
            FMath::Max(1.0f, PatrolAcceptanceRadius),
            true,
            true,
            true,
            false,
            nullptr,
            true);
    }
}

void AAFLeaperEnemy::UpdateAlertBodyTurn(float DeltaSeconds)
{
    if (!GetWorld() || GetWorld()->GetTimeSeconds() < BodyTurnStartTime)
    {
        return;
    }

    FVector ThreatLocation;
    if (!GetCurrentThreatLocation(ThreatLocation))
    {
        return;
    }

    FVector FlatDirection = ThreatLocation - GetActorLocation();
    FlatDirection.Z = 0.0f;
    if (FlatDirection.IsNearlyZero())
    {
        return;
    }

    const FRotator DesiredRotation(0.0f, FlatDirection.Rotation().Yaw, 0.0f);
    SetActorRotation(FMath::RInterpTo(
        GetActorRotation(),
        DesiredRotation,
        FMath::Max(0.0f, DeltaSeconds),
        AlertBodyTurnSpeed));
}

void AAFLeaperEnemy::UpdateAttackPursuit()
{
    if (!GetWorld() || bPounceInProgress)
    {
        return;
    }

    const float Now = GetWorld()->GetTimeSeconds();
    if (Now < NextAttackMoveRequestTime)
    {
        return;
    }
    NextAttackMoveRequestTime = Now + FMath::Max(0.05f, AttackMoveRequestInterval);

    AAIController* AI = Cast<AAIController>(GetController());
    if (!AI)
    {
        return;
    }

    if (VisualTarget.IsValid())
    {
        AActor* Target = VisualTarget.Get();
        const float HorizontalDistance = FVector(
            Target->GetActorLocation().X - GetActorLocation().X,
            Target->GetActorLocation().Y - GetActorLocation().Y,
            0.0f).Size();

        if (HorizontalDistance >= MinPounceRange &&
            HorizontalDistance <= MaxPounceRange &&
            Now >= NextPounceAllowedTime)
        {
            StopAIMovement();
            if (TryPounceAt(Target))
            {
                return;
            }
        }

        AI->MoveToActor(
            Target,
            FMath::Max(1.0f, AttackMoveAcceptanceRadius),
            true,
            true,
            true,
            nullptr,
            true);
        return;
    }

    if (bHasLastSeenLocation)
    {
        AI->MoveToLocation(
            LastSeenLocation,
            FMath::Max(1.0f, AttackMoveAcceptanceRadius),
            true,
            true,
            true,
            false,
            nullptr,
            true);
    }
}

void AAFLeaperEnemy::UpdateBehaviourMovement(float DeltaSeconds)
{
    if (!bEnableAutonomousBehaviour || !GetWorld())
    {
        return;
    }

    switch (AlertState)
    {
        case EAFLeaperAlertState::Scanning:
            UpdateScanningPatrol();
            break;

        case EAFLeaperAlertState::Alert:
            UpdateAlertBodyTurn(DeltaSeconds);
            break;

        case EAFLeaperAlertState::Attacking:
            UpdateAttackPursuit();
            break;

        default:
            break;
    }
}

bool AAFLeaperEnemy::TryPounceAt(AActor* TargetActor)
{
    if (!TargetActor || bPounceInProgress || !GetWorld())
    {
        return false;
    }

    const float Now = GetWorld()->GetTimeSeconds();
    if (Now < NextPounceAllowedTime)
    {
        return false;
    }

    const FVector Start = GetActorLocation();
    const FVector Target = TargetActor->GetActorLocation();
    const FVector Delta = Target - Start;
    const float HorizontalDistance = FVector(Delta.X, Delta.Y, 0.0f).Size();

    if (HorizontalDistance < MinPounceRange ||
        HorizontalDistance > MaxPounceRange)
    {
        return false;
    }

    NotifyPlayerSeen(TargetActor);

    const float FlightTime = FMath::Max(0.25f, PounceFlightTime);
    const float GravityZ = GetWorld()->GetGravityZ();

    FVector LaunchVelocity = Delta / FlightTime;
    LaunchVelocity.Z -= 0.5f * GravityZ * FlightTime;

    bPounceInProgress = true;
    NextPounceAllowedTime = Now + FMath::Max(0.0f, PounceCooldown);
    SetAlertState(EAFLeaperAlertState::Attacking);
    StopAIMovement();

    if (PounceAnimation && GetMesh())
    {
        GetMesh()->PlayAnimation(PounceAnimation, false);
    }

    GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    LaunchCharacter(LaunchVelocity, true, true);
    return true;
}

void AAFLeaperEnemy::Landed(const FHitResult& Hit)
{
    Super::Landed(Hit);

    if (!bPounceInProgress)
    {
        return;
    }

    bPounceInProgress = false;
    SetAlertState(VisualTarget.IsValid()
        ? EAFLeaperAlertState::Attacking
        : EAFLeaperAlertState::Alert);
    // If the state stayed Attacking, explicitly leave the one-shot pounce
    // animation and return to the red pursuit crawl.
    PlayStateAnimation();

    UGameplayStatics::ApplyRadialDamage(
        this,
        LandingDamage,
        GetActorLocation(),
        LandingDamageRadius,
        nullptr,
        TArray<AActor*>(),
        this,
        GetController(),
        true);
}
