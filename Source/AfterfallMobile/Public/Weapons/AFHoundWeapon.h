#pragma once
#include "CoreMinimal.h"
#include "Weapons/AFWeaponBase.h"
#include "AFHoundWeapon.generated.h"

UCLASS(Blueprintable)
class AFTERFALLMOBILE_API AAFHoundWeapon : public AAFWeaponBase
{
    GENERATED_BODY()
public:
    AAFHoundWeapon();
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Preview") bool bShowPrimitiveBlockout = true;
protected:
    virtual void BeginPlay() override;
    UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> PreviewParts;
};
