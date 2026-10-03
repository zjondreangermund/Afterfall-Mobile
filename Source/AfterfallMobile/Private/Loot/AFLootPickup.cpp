#include "Loot/AFLootPickup.h"

#include "Components/StaticMeshComponent.h"
#include "Inventory/AFInventoryComponent.h"

AAFLootPickup::AAFLootPickup()
{
    PrimaryActorTick.bCanEverTick = false;

    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
    SetRootComponent(Mesh);
    Mesh->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
}

bool AAFLootPickup::Collect(AActor* Collector)
{
    if (!Collector)
    {
        return false;
    }

    UAFInventoryComponent* Inventory = Collector->FindComponentByClass<UAFInventoryComponent>();
    if (!Inventory)
    {
        return false;
    }

    if (Inventory->GetUsedSlots() >= Inventory->MaxSlots && Inventory->GetItemCount(ItemId) == 0)
    {
        return false;
    }

    Inventory->AddItem(ItemId, Quantity);
    Destroy();
    return true;
}
