#pragma once

// Engine-independent path timing, shared by runtime movement and regression tests.
namespace AFTraversalPath
{
inline float Smooth(float Value)
{
    const float T = Value < 0.f ? 0.f : (Value > 1.f ? 1.f : Value);
    return T * T * (3.f - 2.f * T);
}

struct Progress
{
    float Forward;
    float Rise;
    float Settle;
};

inline Progress Evaluate(float Alpha)
{
    // Clear the near face before crossing it; settle only after crossing.
    return {Smooth((Alpha - 0.35f) / 0.40f),
            Smooth(Alpha / 0.35f),
            Smooth((Alpha - 0.75f) / 0.25f)};
}
}
