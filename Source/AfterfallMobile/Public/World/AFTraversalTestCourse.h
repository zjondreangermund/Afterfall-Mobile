#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AFTraversalTestCourse.generated.h"

class USceneComponent;
class UInstancedStaticMeshComponent;

/**
 * Editor-only friendly greybox parkour course used to test the player movement
 * without needing a finished map. The character can auto-spawn one in PIE.
 */
UCLASS()
class AFTERFALLMOBILE_API AAFTraversalTestCourse : public AActor
{
    GENERATED_BODY()

public:
    AAFTraversalTestCourse();

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Traversal Test")
    TObjectPtr<USceneComponent> Root;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Traversal Test")
    TObjectPtr<UInstancedStaticMeshComponent> Geometry;

private:
    void AddBox(
        const FVector& Center,
        const FVector& Size,
        const FRotator& Rotation = FRotator::ZeroRotator);
};
