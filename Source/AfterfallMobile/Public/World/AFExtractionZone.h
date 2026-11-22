#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AFExtractionZone.generated.h"

class UBoxComponent;
class UAFPowerCircuitComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FAFExtractionComplete, AActor*, ExtractedActor);

UCLASS()
class AFTERFALLMOBILE_API AAFExtractionZone : public AActor
{
    GENERATED_BODY()

public:
    AAFExtractionZone();

    UPROPERTY(BlueprintAssignable, Category="Afterfall|Extraction")
    FAFExtractionComplete OnExtractionComplete;

    /** Optional circuit actor. When assigned, the named consumer must remain powered. */
    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category="Afterfall|Power")
    TObjectPtr<AActor> PowerCircuitActor;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Afterfall|Power")
    FName PowerConsumer = TEXT("ExtractionLift");

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
    bool HasExtractionPower() const;

    UFUNCTION()
    void HandleCircuitChanged();
};
