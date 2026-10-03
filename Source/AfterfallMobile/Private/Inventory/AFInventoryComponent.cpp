#include "Inventory/AFInventoryComponent.h"

UAFInventoryComponent::UAFInventoryComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UAFInventoryComponent::AddItem(FName ItemId, int32 Quantity)
{
    if (ItemId.IsNone() || Quantity <= 0)
    {
        return;
    }

    int32& Count = Items.FindOrAdd(ItemId);
    Count += Quantity;
}

bool UAFInventoryComponent::RemoveItem(FName ItemId, int32 Quantity)
{
    if (Quantity <= 0)
    {
        return false;
    }

    int32* Count = Items.Find(ItemId);
    if (!Count || *Count < Quantity)
    {
        return false;
    }

    *Count -= Quantity;
    if (*Count <= 0)
    {
        Items.Remove(ItemId);
    }

    return true;
}

int32 UAFInventoryComponent::GetItemCount(FName ItemId) const
{
    if (const int32* Count = Items.Find(ItemId))
    {
        return *Count;
    }

    return 0;
}

void UAFInventoryComponent::ClearRaidInventory()
{
    Items.Reset();
}

int32 UAFInventoryComponent::GetUsedSlots() const
{
    return Items.Num();
}
