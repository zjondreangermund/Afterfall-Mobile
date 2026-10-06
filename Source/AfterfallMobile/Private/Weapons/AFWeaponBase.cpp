#include "Weapons/AFWeaponBase.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/AFHealthComponent.h"
#include "Enemies/AFLeaperEnemy.h"
#include "Enemies/AFRigEnemyBase.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Particles/ParticleSystem.h"
#include "Sound/SoundBase.h"

AAFWeaponBase::AAFWeaponBase()
{
    PrimaryActorTick.bCanEverTick = true;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("WeaponRoot")));
    WeaponMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WeaponMesh"));
    WeaponMesh->SetupAttachment(RootComponent);
    WeaponMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    MuzzleFallback = CreateDefaultSubobject<USceneComponent>(TEXT("MuzzleFallback"));
    MuzzleFallback->SetupAttachment(RootComponent);
    MuzzleFallback->SetRelativeLocation(FVector(78,0,14));
    MuzzleLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("MuzzleFlashPreview"));
    MuzzleLight->SetupAttachment(MuzzleFallback);
    MuzzleLight->SetIntensity(1500.f);
    MuzzleLight->SetAttenuationRadius(100.f);
    MuzzleLight->SetLightColor(FLinearColor(1.f,.35f,.05f));
    MuzzleLight->SetCastShadows(false);
    MuzzleLight->SetVisibility(false);
    HeatIndicator = CreateDefaultSubobject<UPointLightComponent>(TEXT("HeatIndicatorPreview"));
    HeatIndicator->SetupAttachment(RootComponent);
    HeatIndicator->SetRelativeLocation(FVector(45,-6,14));
    HeatIndicator->SetIntensity(20.f);
    HeatIndicator->SetAttenuationRadius(15.f);
    HeatIndicator->SetCastShadows(false);
}

AFWeapon::Rules AAFWeaponBase::Rules() const
{
    AFWeapon::Rules R;
    R.Capacity = FMath::Max(1,Tuning.MagazineCapacity);
    R.Interval = 60.f / FMath::Clamp(Tuning.RoundsPerMinute,1.f,6000.f);
    R.ReloadSeconds = FMath::Max(.01f,Tuning.ReloadSeconds);
    R.HeatPerShot = FMath::Max(0.f,Tuning.HeatPerShot);
    R.MaxHeat = FMath::Max(1.f,Tuning.MaxHeat);
    R.CoolPerSecond = FMath::Max(0.f,Tuning.CoolPerSecond);
    R.CoolDelay = FMath::Max(0.f,Tuning.CoolingDelay);
    R.UnlockHeat = FMath::Clamp(Tuning.ResumeHeat,0.f,R.MaxHeat*.95f);
    return R;
}

void AAFWeaponBase::BeginPlay()
{
    Super::BeginPlay();
    State.Reset(Rules(), Tuning.InitialReserve);
    BroadcastState();
}

void AAFWeaponBase::EndPlay(const EEndPlayReason::Type Reason)
{
    StopFire();
    Super::EndPlay(Reason);
}

void AAFWeaponBase::SetEquippedPawn(APawn* Pawn)
{
    StopFire();
    CancelReload();
    SetAiming(false);
    SetOwner(Pawn);
    SetInstigator(Pawn);
}

void AAFWeaponBase::Tick(float Dt)
{
    Super::Tick(Dt);
    APawn* Pawn = GetInstigator();
    const UAFHealthComponent* Health = Pawn ? Pawn->FindComponentByClass<UAFHealthComponent>() : nullptr;
    if (!Pawn || !Pawn->GetController() || (Health && Health->IsDead()))
    {
        StopFire();
        CancelReload();
    }
    const bool WasReloading = State.Reloading;
    const float OldHeat = State.Heat;
    const bool WasHot = State.Overheated;
    State.Advance(Dt, Rules());
    FlashRemaining = FMath::Max(0.f,FlashRemaining-Dt);
    MuzzleLight->SetVisibility(FlashRemaining>0.f);
    if (WasReloading && !State.Reloading)
    {
        OnReloadFinished(false);
        BroadcastState();
    }
    if (!FMath::IsNearlyEqual(OldHeat,State.Heat) || WasHot!=State.Overheated) BroadcastState();
    // Never catch up missed frames with a burst of damage in one frame.
    if (bTriggerHeld && Tuning.bAutomatic) TryFire();
}

float AAFWeaponBase::GetHeatNormalized() const { return FMath::Clamp(State.Heat/FMath::Max(1.f,Tuning.MaxHeat),0.f,1.f); }

void AAFWeaponBase::BroadcastState()
{
    const float Heat = GetHeatNormalized();
    const FLinearColor Color = FMath::Lerp(FLinearColor(1.f,.5f,.05f),FLinearColor(1.f,.01f,0),Heat);
    HeatIndicator->SetLightColor(Color);
    HeatIndicator->SetVisibility(Heat>.01f);
    OnHeatChanged(Heat,State.Overheated);
    OnStateChanged.Broadcast();
}

FTransform AAFWeaponBase::GetMuzzleTransform() const
{
    return WeaponMesh->DoesSocketExist(MuzzleSocket) ? WeaponMesh->GetSocketTransform(MuzzleSocket) : MuzzleFallback->GetComponentTransform();
}

void AAFWeaponBase::StartFire() { if (!bTriggerHeld) { bTriggerHeld=true; TryFire(); } }
void AAFWeaponBase::StopFire() { bTriggerHeld=false; }
void AAFWeaponBase::SetAiming(bool Value) { if (bAiming!=Value) { bAiming=Value; OnAimChanged(Value); } }

bool AAFWeaponBase::Reload()
{
    APawn* Pawn = GetInstigator();
    const UAFHealthComponent* Health = Pawn ? Pawn->FindComponentByClass<UAFHealthComponent>() : nullptr;
    if (!Pawn || !Pawn->GetController() || (Health && Health->IsDead()) || !State.Reload(Rules())) return false;
    StopFire();
    if (ReloadSound) UGameplayStatics::PlaySoundAtLocation(this,ReloadSound,GetActorLocation());
    OnReloadStarted();
    BroadcastState();
    return true;
}
void AAFWeaponBase::CancelReload()
{
    if (State.Reloading) { State.CancelReload(); OnReloadFinished(true); BroadcastState(); }
}
void AAFWeaponBase::AddReserveAmmo(int32 Amount)
{
    if (Amount>0) { State.Reserve=static_cast<int32>(FMath::Min<int64>(MAX_int32,static_cast<int64>(State.Reserve)+Amount)); BroadcastState(); }
}

bool AAFWeaponBase::TryFire()
{
    APawn* Pawn = GetInstigator();
    if (!Pawn || GetOwner()!=Pawn || !Pawn->GetController() || !GetWorld()) return false;
    const UAFHealthComponent* Health = Pawn->FindComponentByClass<UAFHealthComponent>();
    if (Health && Health->IsDead()) return false;
    if (!State.Shoot(Rules())) return false;
    FVector View; FRotator Rotation;
    Pawn->GetController()->GetPlayerViewPoint(View,Rotation);
    const float Spread = FMath::Clamp(bAiming?Tuning.AimSpreadDegrees:Tuning.HipSpreadDegrees,0.f,10.f);
    const FVector ViewDirection = FMath::VRandCone(Rotation.Vector(),FMath::DegreesToRadians(Spread));
    const float Range = FMath::Max(100.f,Tuning.EffectiveRange);
    FCollisionQueryParams Params(SCENE_QUERY_STAT(AFWeaponFire),true,Pawn);
    Params.AddIgnoredActor(this);
    FHitResult CameraHit, Hit;
    FVector AimPoint = View+ViewDirection*Range;
    if (GetWorld()->LineTraceSingleByChannel(CameraHit,View,AimPoint,ECC_Visibility,Params)) AimPoint=CameraHit.ImpactPoint;
    const FTransform Muzzle = GetMuzzleTransform();
    const FVector Start = Muzzle.GetLocation();
    FVector Direction = (AimPoint-Start).GetSafeNormal();
    if (FVector::DotProduct(Direction,ViewDirection)<=0) Direction=ViewDirection;
    // Stop a muzzle poking through a wall from shooting beyond that wall.
    bool bHit = GetWorld()->LineTraceSingleByChannel(Hit,Pawn->GetActorLocation(),Start,ECC_Visibility,Params);
    if (!bHit) bHit=GetWorld()->LineTraceSingleByChannel(Hit,Start,Start+Direction*Range,ECC_Visibility,Params);
    for (TActorIterator<AAFLeaperEnemy> It(GetWorld()); It; ++It)
    {
        It->NotifyGunshotHeard(Start, 1.f);
    }
    for (TActorIterator<AAFRigEnemyBase> It(GetWorld()); It; ++It)
    {
        It->NotifyGunshotHeard(Start, 1.f);
    }
    if (bHit && Hit.GetActor()) UGameplayStatics::ApplyPointDamage(Hit.GetActor(),FMath::Max(0.f,Tuning.Damage),Direction,Hit,Pawn->GetController(),this,nullptr);
    MuzzleLight->SetWorldLocation(Start);
    FlashRemaining=.045f;
    MuzzleLight->SetVisibility(true);
    if (MuzzleEffect) UGameplayStatics::SpawnEmitterAtLocation(GetWorld(),MuzzleEffect,Muzzle);
    if (FireSound) UGameplayStatics::PlaySoundAtLocation(this,FireSound,Start);
    if (APlayerController* PC=Cast<APlayerController>(Pawn->GetController()))
    {
        FRotator Recoil=PC->GetControlRotation();
        Recoil.Pitch=FMath::ClampAngle(Recoil.Pitch+FMath::Max(0.f,Tuning.PitchRecoil),-80.f,80.f);
        Recoil.Yaw+=FMath::FRandRange(-FMath::Abs(Tuning.YawRecoil),FMath::Abs(Tuning.YawRecoil));
        PC->SetControlRotation(Recoil);
    }
    OnWeaponFired(Muzzle,Hit);
    BroadcastState();
    return true;
}
