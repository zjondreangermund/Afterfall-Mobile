#include "World/AFExtractionZone.h"

#include "Components/BoxComponent.h"
#include "Components/AFPowerCircuitComponent.h"
#include "GameFramework/Character.h"
#include "TimerManager.h"

AAFExtractionZone::AAFExtractionZone()
{
    PrimaryActorTick.bCanEverTick = false;

    ExtractionVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("ExtractionVolume"));
    SetRootComponent(ExtractionVolume);
    ExtractionVolume->SetBoxExtent(FVector(250.0f, 250.0f, 150.0f));
    ExtractionVolume->SetCollisionProfileName(TEXT("Trigger"));
}

void AAFExtractionZone::BeginPlay()
{
    Super::BeginPlay();

    ExtractionVolume->OnComponentBeginOverlap.AddDynamic(this, &AAFExtractionZone::HandleBeginOverlap);
    ExtractionVolume->OnComponentEndOverlap.AddDynamic(this, &AAFExtractionZone::HandleEndOverlap);
    if (PowerCircuitActor)
    {
        if (auto* Circuit = PowerCircuitActor->FindComponentByClass<UAFPowerCircuitComponent>())
        {
            Circuit->OnCircuitChanged.AddDynamic(this, &AAFExtractionZone::HandleCircuitChanged);
        }
    }
}

void AAFExtractionZone::HandleBeginOverlap(
    UPrimitiveComponent* OverlappedComponent,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComponent,
    int32 OtherBodyIndex,
    bool bFromSweep,
    const FHitResult& SweepResult)
{
    const ACharacter* Character = Cast<ACharacter>(OtherActor);
    if (!Character || !Character->IsPlayerControlled() || CurrentActor || !HasExtractionPower())
    {
        return;
    }

    CurrentActor = OtherActor;
    GetWorldTimerManager().SetTimer(
        ExtractionTimer,
        this,
        &AAFExtractionZone::CompleteExtraction,
        HoldSeconds,
        false);
}

void AAFExtractionZone::HandleEndOverlap(
    UPrimitiveComponent* OverlappedComponent,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComponent,
    int32 OtherBodyIndex)
{
    if (OtherActor != CurrentActor)
    {
        return;
    }

    GetWorldTimerManager().ClearTimer(ExtractionTimer);
    CurrentActor = nullptr;
}

void AAFExtractionZone::CompleteExtraction()
{
    if (!IsValid(CurrentActor) || !HasExtractionPower())
    {
        CurrentActor = nullptr;
        return;
    }

    AActor* ExtractedActor = CurrentActor;
    CurrentActor = nullptr;
    OnExtractionComplete.Broadcast(ExtractedActor);
}

bool AAFExtractionZone::HasExtractionPower() const
{
    if (!PowerCircuitActor)
    {
        return true;
    }
    const auto* Circuit = PowerCircuitActor->FindComponentByClass<UAFPowerCircuitComponent>();
    return Circuit && Circuit->IsConsumerPowered(PowerConsumer);
}

void AAFExtractionZone::HandleCircuitChanged()
{
    if (!HasExtractionPower())
    {
        GetWorldTimerManager().ClearTimer(ExtractionTimer);
        CurrentActor = nullptr;
    }
    // Restoring power requires leaving and re-entering the volume to start a fresh countdown.
}
