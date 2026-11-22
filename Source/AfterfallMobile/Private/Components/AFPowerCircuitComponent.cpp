#include "Components/AFPowerCircuitComponent.h"

UAFPowerCircuitComponent::UAFPowerCircuitComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

int32 UAFPowerCircuitComponent::GetAvailablePower() const
{
    int32 Available = Capacity;
    for (const auto& Load : Loads)
    {
        Available -= Load.Value;
    }
    return Available;
}

bool UAFPowerCircuitComponent::SetConsumerPower(FName Consumer, int32 Units, float Disturbance)
{
    if (Consumer.IsNone() || Units <= 0 || !FMath::IsFinite(Disturbance) || Disturbance < 0.f)
    {
        return false;
    }
    const int32* Existing = Loads.Find(Consumer);
    const int32 Previous = Existing ? *Existing : 0;
    // Compare the delta to avoid overflow when adding a replacement load to available power.
    if (Units > Previous && Units - Previous > GetAvailablePower())
    {
        return false;
    }
    if (Previous == Units)
    {
        return true;
    }
    Loads.Add(Consumer, Units);
    OnCircuitChanged.Broadcast();
    if (Units > Previous && Disturbance > 0.f)
    {
        OnDisturbance.Broadcast(Consumer, Disturbance);
    }
    return true;
}

bool UAFPowerCircuitComponent::DisconnectConsumer(FName Consumer)
{
    if (Loads.Remove(Consumer) == 0)
    {
        return false;
    }
    OnCircuitChanged.Broadcast();
    return true;
}

bool UAFPowerCircuitComponent::SetCapacity(int32 Units)
{
    const int32 Used = Capacity - GetAvailablePower();
    if (Units < 0 || Units < Used)
    {
        return false;
    }
    if (Capacity != Units)
    {
        Capacity = Units;
        OnCircuitChanged.Broadcast();
    }
    return true;
}
