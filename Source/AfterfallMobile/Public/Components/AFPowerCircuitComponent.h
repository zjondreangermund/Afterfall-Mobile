#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AFPowerCircuitComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FAFPowerCircuitChanged);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FAFPowerDisturbance, FName, Consumer, float, Strength);

/** Solo prototype circuit. UI and machinery subscribe to changes; no per-frame tick. */
UCLASS(ClassGroup=(Afterfall), meta=(BlueprintSpawnableComponent))
class AFTERFALLMOBILE_API UAFPowerCircuitComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UAFPowerCircuitComponent();

    UFUNCTION(BlueprintCallable, Category="Afterfall|Power")
    bool SetConsumerPower(FName Consumer, int32 Units, float Disturbance);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Power")
    bool DisconnectConsumer(FName Consumer);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Power")
    bool SetCapacity(int32 Units);

    UFUNCTION(BlueprintPure, Category="Afterfall|Power")
    int32 GetAvailablePower() const;

    UFUNCTION(BlueprintPure, Category="Afterfall|Power")
    bool IsConsumerPowered(FName Consumer) const { return Loads.Contains(Consumer); }

    UPROPERTY(BlueprintAssignable, Category="Afterfall|Power")
    FAFPowerCircuitChanged OnCircuitChanged;

    /** Emitted only for a successful new connection or increased load. */
    UPROPERTY(BlueprintAssignable, Category="Afterfall|Power")
    FAFPowerDisturbance OnDisturbance;

private:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Power", meta=(AllowPrivateAccess="true"))
    int32 Capacity = 100;

    UPROPERTY(Transient)
    TMap<FName, int32> Loads;
};
