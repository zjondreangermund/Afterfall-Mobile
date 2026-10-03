#include "Enemies/AFLeaperEnemy.h"

#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SphereComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Loot/AFLootPickup.h"
#include "Materials/MaterialInterface.h"
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
    EnemyId = TEXT("Leaper");

    // Let weapon visibility traces reach the skeletal mesh / weak-point hitboxes
    // instead of being swallowed by the character capsule.
    GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
    GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    GetMesh()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);

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
    }
}

float AAFLeaperEnemy::TakeDamage(
    float DamageAmount,
    FDamageEvent const& DamageEvent,
    AController* EventInstigator,
    AActor* DamageCauser)
{
    float FinalDamage = DamageAmount;

    if (DamageAmount > 0.0f && DamageEvent.IsOfType(FPointDamageEvent::ClassID))
    {
        const FPointDamageEvent& PointEvent =
            static_cast<const FPointDamageEvent&>(DamageEvent);

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

bool AAFLeaperEnemy::TryPounceAt(AActor* TargetActor)
{
    if (!TargetActor || bPounceInProgress || !GetWorld())
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

    const float FlightTime = FMath::Max(0.25f, PounceFlightTime);
    const float GravityZ = GetWorld()->GetGravityZ();

    FVector LaunchVelocity = Delta / FlightTime;
    LaunchVelocity.Z -= 0.5f * GravityZ * FlightTime;

    bPounceInProgress = true;
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
