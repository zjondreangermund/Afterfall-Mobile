#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AFLootPickup.generated.h"

class UStaticMeshComponent;

UCLASS()
class AFTERFALLMOBILE_API AAFLootPickup : public AActor
{
    GENERATED_BODY()

public:
    AAFLootPickup();

    UFUNCTION(BlueprintCallable, Category="Afterfall|Loot")
    bool Collect(AActor* Collector);

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Loot")
    TObjectPtr<UStaticMeshComponent> Mesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Afterfall|Loot")
    FName ItemId = TEXT("Scrap");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Afterfall|Loot", meta=(ClampMin="1"))
    int32 Quantity = 1;
};
