#include "Loot/AFLootPickup.h"

#include "Components/StaticMeshComponent.h"
#include "Inventory/AFInventoryComponent.h"

AAFLootPickup::AAFLootPickup()
{
    PrimaryActorTick.bCanEverTick = false;

    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
    SetRootComponent(Mesh);

    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Mesh->SetCollisionResponseToAllChannels(ECR_Ignore);
    Mesh->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    Mesh->SetGenerateOverlapEvents(true);
}

void AAFLootPickup::ConfigureLoot(FName NewItemId, int32 NewQuantity)
{
    if (!NewItemId.IsNone())
    {
        ItemId = NewItemId;
    }

    Quantity = FMath::Max(1, NewQuantity);
}

void AAFLootPickup::DropWithImpulse(FVector Impulse)
{
    if (!Mesh || !Mesh->GetStaticMesh())
    {
        return;
    }

    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Mesh->SetCollisionObjectType(ECC_PhysicsBody);
    Mesh->SetCollisionResponseToAllChannels(ECR_Ignore);
    Mesh->SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Block);
    Mesh->SetCollisionResponseToChannel(ECC_WorldDynamic, ECR_Block);
    Mesh->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    Mesh->SetGenerateOverlapEvents(true);
    Mesh->SetSimulatePhysics(true);
    Mesh->AddImpulse(Impulse, NAME_None, true);
}

bool AAFLootPickup::Collect(AActor* Collector)
{
    if (!Collector)
    {
        return false;
    }

    UAFInventoryComponent* Inventory =
        Collector->FindComponentByClass<UAFInventoryComponent>();

    if (!Inventory)
    {
        return false;
    }

    if (Inventory->GetUsedSlots() >= Inventory->MaxSlots &&
        Inventory->GetItemCount(ItemId) == 0)
    {
        return false;
    }

    Inventory->AddItem(ItemId, Quantity);
    Destroy();
    return true;
}
