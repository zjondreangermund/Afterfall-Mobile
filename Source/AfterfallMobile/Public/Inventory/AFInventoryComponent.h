#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AFInventoryComponent.generated.h"

UCLASS(ClassGroup=(Afterfall), meta=(BlueprintSpawnableComponent))
class AFTERFALLMOBILE_API UAFInventoryComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UAFInventoryComponent();

    UFUNCTION(BlueprintCallable, Category="Afterfall|Inventory")
    void AddItem(FName ItemId, int32 Quantity = 1);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Inventory")
    bool RemoveItem(FName ItemId, int32 Quantity = 1);

    UFUNCTION(BlueprintPure, Category="Afterfall|Inventory")
    int32 GetItemCount(FName ItemId) const;

    UFUNCTION(BlueprintCallable, Category="Afterfall|Inventory")
    void ClearRaidInventory();

    UFUNCTION(BlueprintPure, Category="Afterfall|Inventory")
    int32 GetUsedSlots() const;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Inventory", meta=(ClampMin="1"))
    int32 MaxSlots = 12;

private:
    UPROPERTY(VisibleInstanceOnly, Category="Afterfall|Inventory")
    TMap<FName, int32> Items;
};
