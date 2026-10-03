#include "World/AFExtractionZone.h"

#include "Components/BoxComponent.h"
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
}

void AAFExtractionZone::HandleBeginOverlap(
    UPrimitiveComponent* OverlappedComponent,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComponent,
    int32 OtherBodyIndex,
    bool bFromSweep,
    const FHitResult& SweepResult)
{
    if (!OtherActor || !OtherActor->IsA<ACharacter>())
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
    if (!CurrentActor)
    {
        return;
    }

    AActor* ExtractedActor = CurrentActor;
    CurrentActor = nullptr;
    OnExtractionComplete.Broadcast(ExtractedActor);
}
