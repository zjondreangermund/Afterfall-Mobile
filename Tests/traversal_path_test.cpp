#include "Player/AFTraversalPath.h"
#include <cassert>
#include <cmath>
#include <iostream>

static bool Near(float A, float B) { return std::abs(A - B) < 0.001f; }

int main()
{
    using namespace AFTraversalPath;
    // Endpoints, clamped times and phase continuity.
    for (float T : {-1.f, 0.f})
    {
        const auto P = Evaluate(T);
        assert(Near(P.Forward, 0) && Near(P.Rise, 0) && Near(P.Settle, 0));
    }
    for (float T : {1.f, 2.f})
    {
        const auto P = Evaluate(T);
        assert(Near(P.Forward, 1) && Near(P.Rise, 1) && Near(P.Settle, 1));
    }
    for (float Boundary : {0.35f, 0.75f})
    {
        const auto Before = Evaluate(Boundary - 0.00001f);
        const auto After = Evaluate(Boundary + 0.00001f);
        assert(Near(Before.Forward, After.Forward));
        assert(Near(Before.Rise, After.Rise));
        assert(Near(Before.Settle, After.Settle));
    }

    // Capsule bottom must clear each wall before any forward travel, and
    // settling must never start while the capsule is still crossing the wall.
    for (float Height : {60.f, 100.f, 145.f, 170.f, 260.f})
    for (bool Vault : {false, true})
    for (float HalfHeight : {88.f, 96.f})
    {
        const float StartZ = HalfHeight;
        const float ClearanceZ = Height + HalfHeight + 3.f;
        const float EndZ = Vault ? StartZ : ClearanceZ;
        float PreviousForward = 0.f;
        for (int Frame = 0; Frame <= 1000; ++Frame)
        {
            const auto P = Evaluate(Frame / 1000.f);
            const float Z = StartZ + (ClearanceZ - StartZ) * P.Rise
                + (EndZ - ClearanceZ) * P.Settle;
            assert(P.Forward >= PreviousForward);
            PreviousForward = P.Forward;
            if (P.Forward > 0.f && P.Forward < 1.f)
            {
                assert(Z - HalfHeight >= Height + 2.99f);
            }
            if (P.Settle > 0.f) assert(Near(P.Forward, 1.f));
        }
    }
    std::cout << "Traversal path regression checks passed\n";
}
