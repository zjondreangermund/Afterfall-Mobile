#include "World/AFTraversalTestCourse.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

AAFTraversalTestCourse::AAFTraversalTestCourse()
{
    PrimaryActorTick.bCanEverTick = false;

    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    Root->SetMobility(EComponentMobility::Static);
    SetRootComponent(Root);

    Geometry = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Geometry"));
    Geometry->SetupAttachment(Root);
    Geometry->SetMobility(EComponentMobility::Static);
    Geometry->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Geometry->SetCollisionProfileName(TEXT("BlockAll"));
    Geometry->SetGenerateOverlapEvents(false);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(
        TEXT("/Engine/BasicShapes/Cube.Cube"));

    if (CubeMesh.Succeeded())
    {
        Geometry->SetStaticMesh(CubeMesh.Object);
    }

    // Main floor / terrain strip.
    AddBox(FVector(1800.f, 0.f, -10.f), FVector(3800.f, 1400.f, 20.f));

    // Small obstacle: should vault cleanly.
    AddBox(FVector(520.f, 0.f, 30.f), FVector(55.f, 420.f, 60.f));

    // Waist-high wall: vault / fast mantle.
    AddBox(FVector(900.f, 0.f, 50.f), FVector(70.f, 480.f, 100.f));

    // Chest-high wall: proper mantle.
    AddBox(FVector(1290.f, 0.f, 85.f), FVector(90.f, 520.f, 170.f));

    // Tall platform: jump toward it, auto-grab, hang, then press Space to climb.
    AddBox(FVector(1760.f, 0.f, 130.f), FVector(360.f, 620.f, 260.f));

    // Window test wall. Low sill + side pillars + lintel leaves a clear opening.
    AddBox(FVector(2350.f, 0.f, 34.f), FVector(65.f, 240.f, 68.f));   // sill
    AddBox(FVector(2350.f, -260.f, 125.f), FVector(65.f, 220.f, 250.f));
    AddBox(FVector(2350.f, 260.f, 125.f), FVector(65.f, 220.f, 250.f));
    AddBox(FVector(2350.f, 0.f, 235.f), FVector(65.f, 300.f, 50.f));  // lintel

    // Small clutter for contextual vault testing.
    AddBox(FVector(2780.f, -170.f, 40.f), FVector(110.f, 110.f, 80.f));
    AddBox(FVector(2920.f, 120.f, 55.f), FVector(140.f, 140.f, 110.f));
    AddBox(FVector(3090.f, -80.f, 32.5f), FVector(90.f, 90.f, 65.f));

    // Rough terrain / ramp section.
    AddBox(
        FVector(3290.f, 0.f, 35.f),
        FVector(420.f, 520.f, 38.f),
        FRotator(0.f, 0.f, -10.f));

    AddBox(FVector(3520.f, 0.f, 75.f), FVector(260.f, 520.f, 150.f));

    // Side platforms so the player can jump between uneven heights.
    AddBox(FVector(1500.f, 470.f, 45.f), FVector(360.f, 260.f, 90.f));
    AddBox(FVector(1920.f, 470.f, 90.f), FVector(300.f, 260.f, 180.f));
}

void AAFTraversalTestCourse::AddBox(
    const FVector& Center,
    const FVector& Size,
    const FRotator& Rotation)
{
    if (!Geometry)
    {
        return;
    }

    const FVector Scale(
        FMath::Max(1.0f, Size.X) / 100.0f,
        FMath::Max(1.0f, Size.Y) / 100.0f,
        FMath::Max(1.0f, Size.Z) / 100.0f);

    Geometry->AddInstance(FTransform(Rotation, Center, Scale));
}
