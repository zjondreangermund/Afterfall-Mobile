#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AFExtractionZone.generated.h"

class UBoxComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FAFExtractionComplete, AActor*, ExtractedActor);

UCLASS()
class AFTERFALLMOBILE_API AAFExtractionZone : public AActor
{
    GENERATED_BODY()

public:
    AAFExtractionZone();

    UPROPERTY(BlueprintAssignable, Category="Afterfall|Extraction")
    FAFExtractionComplete OnExtractionComplete;

protected:
    virtual void BeginPlay() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Extraction")
    TObjectPtr<UBoxComponent> ExtractionVolume;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Afterfall|Extraction", meta=(ClampMin="0.5"))
    float HoldSeconds = 8.0f;

private:
    UPROPERTY()
    TObjectPtr<AActor> CurrentActor;

    FTimerHandle ExtractionTimer;

    UFUNCTION()
    void HandleBeginOverlap(
        UPrimitiveComponent* OverlappedComponent,
        AActor* OtherActor,
        UPrimitiveComponent* OtherComponent,
        int32 OtherBodyIndex,
        bool bFromSweep,
        const FHitResult& SweepResult);

    UFUNCTION()
    void HandleEndOverlap(
        UPrimitiveComponent* OverlappedComponent,
        AActor* OtherActor,
        UPrimitiveComponent* OtherComponent,
        int32 OtherBodyIndex);

    void CompleteExtraction();
};
