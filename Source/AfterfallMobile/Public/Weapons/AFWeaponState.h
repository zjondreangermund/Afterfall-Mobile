#pragma once
#include <algorithm>

// Engine-independent state, shared by runtime and the executable regression test.
namespace AFWeapon
{
struct Rules
{
    int Capacity = 30;
    float Interval = .12f, ReloadSeconds = 2.2f;
    float HeatPerShot = 8.f, MaxHeat = 100.f, CoolPerSecond = 18.f;
    float CoolDelay = .35f, UnlockHeat = 35.f;
};
struct State
{
    int Magazine = 30, Reserve = 120;
    float Heat = 0, FireWait = 0, CoolWait = 0, ReloadWait = 0;
    bool Reloading = false, Overheated = false;
    void Reset(const Rules& R, int InitialReserve)
    {
        *this = State{};
        Magazine = std::max(1, R.Capacity);
        Reserve = std::max(0, InitialReserve);
    }
    bool Shoot(const Rules& R)
    {
        if (Reloading || Overheated || Magazine <= 0 || FireWait > .00001f) return false;
        --Magazine;
        FireWait = std::max(.01f, R.Interval);
        Heat = std::min(std::max(1.f, R.MaxHeat), Heat + std::max(0.f, R.HeatPerShot));
        CoolWait = std::max(0.f, R.CoolDelay);
        Overheated = Heat >= std::max(1.f, R.MaxHeat);
        return true;
    }
    bool Reload(const Rules& R)
    {
        if (Reloading || Reserve <= 0 || Magazine >= std::max(1, R.Capacity)) return false;
        Reloading = true;
        ReloadWait = std::max(.01f, R.ReloadSeconds);
        return true;
    }
    void CancelReload() { Reloading = false; ReloadWait = 0; }
    void Advance(float Delta, const Rules& R)
    {
        const float Dt = std::max(0.f, Delta);
        FireWait = std::max(0.f, FireWait - Dt);
        const float CoolingTime = std::max(0.f, Dt - CoolWait);
        CoolWait = std::max(0.f, CoolWait - Dt);
        Heat = std::max(0.f, Heat - CoolingTime * std::max(0.f, R.CoolPerSecond));
        if (Overheated && Heat <= std::max(0.f, std::min(R.UnlockHeat, R.MaxHeat * .95f))) Overheated = false;
        if (Reloading)
        {
            ReloadWait -= Dt;
            if (ReloadWait <= 0)
            {
                const int Transfer = std::min(Reserve, std::max(0, R.Capacity - Magazine));
                Magazine += Transfer;
                Reserve -= Transfer;
                CancelReload();
            }
        }
    }
};
}
