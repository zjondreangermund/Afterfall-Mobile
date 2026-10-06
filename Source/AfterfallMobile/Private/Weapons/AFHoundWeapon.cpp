#include "Weapons/AFHoundWeapon.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

AAFHoundWeapon::AAFHoundWeapon()
{
    WeaponId=TEXT("AF01_HOUND");
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    // Visible fallback, no external art dependency. Origin is the right-hand grip.
    auto AddPart=[this](const TCHAR* Name,FVector Location,FVector Size)
    {
        UStaticMeshComponent* Part=CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Part->SetupAttachment(RootComponent);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetRelativeLocation(Location);
        Part->SetRelativeScale3D(Size/100.f);
        if (Cube.Succeeded()) Part->SetStaticMesh(Cube.Object);
        PreviewParts.Add(Part);
    };
    AddPart(TEXT("PreviewReceiver"),FVector(18,0,14),FVector(40,9,13));
    AddPart(TEXT("PreviewForebody"),FVector(55,0,14),FVector(32,8,10));
    AddPart(TEXT("PreviewMuzzle"),FVector(75,0,14),FVector(6,11,13));
    AddPart(TEXT("PreviewStockUpper"),FVector(-21,0,16),FVector(32,5,5));
    AddPart(TEXT("PreviewStockLower"),FVector(-21,0,1),FVector(32,4,3));
    AddPart(TEXT("PreviewStockEnd"),FVector(-36,0,8),FVector(4,7,23));
    AddPart(TEXT("PreviewGrip"),FVector(0,0,-2),FVector(6,6,19));
    AddPart(TEXT("PreviewMagazine"),FVector(22,-6,-5),FVector(10,6,25));
    AddPart(TEXT("PreviewOptic"),FVector(12,0,25),FVector(15,6,8));
}
void AAFHoundWeapon::BeginPlay()
{
    Super::BeginPlay();
    for (UStaticMeshComponent* Part:PreviewParts) Part->SetVisibility(bShowPrimitiveBlockout);
}
