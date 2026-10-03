#include "Game/AFGameModeBase.h"

#include "Player/AFCharacter.h"

AAFGameModeBase::AAFGameModeBase()
{
    DefaultPawnClass = AAFCharacter::StaticClass();
}
