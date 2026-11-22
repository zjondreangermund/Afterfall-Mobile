#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Components/AFPowerCircuitComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAFPowerCircuitTest, "Afterfall.Blackout.PowerChoice",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAFPowerCircuitTest::RunTest(const FString& Parameters)
{
    auto* Circuit = NewObject<UAFPowerCircuitComponent>();
    TestTrue(TEXT("Loot room takes 60 units"), Circuit->SetConsumerPower(TEXT("Loot"), 60, 20.f));
    TestFalse(TEXT("Lift cannot also take 60"), Circuit->SetConsumerPower(TEXT("Lift"), 60, 40.f));
    TestEqual(TEXT("Rejected load leaves budget intact"), Circuit->GetAvailablePower(), 40);
    TestFalse(TEXT("Capacity cannot strand active consumers"), Circuit->SetCapacity(50));
    TestTrue(TEXT("Disconnect loot room"), Circuit->DisconnectConsumer(TEXT("Loot")));
    TestTrue(TEXT("Lift can now run"), Circuit->SetConsumerPower(TEXT("Lift"), 60, 40.f));
    TestTrue(TEXT("Repeated activation is idempotent"), Circuit->SetConsumerPower(TEXT("Lift"), 60, 40.f));
    TestEqual(TEXT("Repeated activation costs nothing extra"), Circuit->GetAvailablePower(), 40);
    TestTrue(TEXT("Load can be reduced"), Circuit->SetConsumerPower(TEXT("Lift"), 20, 0.f));
    TestEqual(TEXT("Reduction returns capacity"), Circuit->GetAvailablePower(), 80);
    TestFalse(TEXT("Negative load rejected"), Circuit->SetConsumerPower(TEXT("Invalid"), -10, 0.f));
    TestFalse(TEXT("Unnamed load rejected"), Circuit->SetConsumerPower(NAME_None, 10, 0.f));
    TestFalse(TEXT("Zero load rejected; use disconnect"), Circuit->SetConsumerPower(TEXT("Lift"), 0, 0.f));
    TestFalse(TEXT("Negative disturbance rejected"), Circuit->SetConsumerPower(TEXT("Other"), 10, -1.f));
    TestEqual(TEXT("Invalid inputs preserve capacity"), Circuit->GetAvailablePower(), 80);
    return !HasAnyErrors();
}
#endif
