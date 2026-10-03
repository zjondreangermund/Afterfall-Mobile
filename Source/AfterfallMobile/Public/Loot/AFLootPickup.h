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

    UFUNCTION(BlueprintCallable, Category="Afterfall|Loot")
    void ConfigureLoot(FName NewItemId, int32 NewQuantity = 1);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Loot")
    void DropWithImpulse(FVector Impulse);

    UFUNCTION(BlueprintPure, Category="Afterfall|Loot")
    FName GetItemId() const { return ItemId; }

    UFUNCTION(BlueprintPure, Category="Afterfall|Loot")
    int32 GetQuantity() const { return Quantity; }

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Loot")
    TObjectPtr<UStaticMeshComponent> Mesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Afterfall|Loot")
    FName ItemId = TEXT("Scrap");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Afterfall|Loot", meta=(ClampMin="1"))
    int32 Quantity = 1;
};
