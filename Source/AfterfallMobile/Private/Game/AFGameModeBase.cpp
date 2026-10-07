#include "Game/AFGameModeBase.h"

#include "Player/AFCharacter.h"
#include "UObject/ConstructorHelpers.h"

AAFGameModeBase::AAFGameModeBase()
{
    // Prefer the project's configured Blueprint pawn so PIE/gameplay uses
    // Manny, ABP_Afterfall_Rifle, HOUND setup, camera tuning and any local
    // Blueprint defaults. Fall back to the native character if the asset is
    // unavailable (for example on a clean source-only checkout).
    static ConstructorHelpers::FClassFinder<AAFCharacter> PlayerPawnBP(
        TEXT("/Game/Afterfall/Characters/BP_AFCharacter"));

    if (PlayerPawnBP.Succeeded())
    {
        DefaultPawnClass = PlayerPawnBP.Class;
    }
    else
    {
        DefaultPawnClass = AAFCharacter::StaticClass();
    }
}
