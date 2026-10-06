#include "Weapons/AFWeaponState.h"
#include <cassert>
#include <cmath>
#include <iostream>

int main()
{
    AFWeapon::Rules R;
    AFWeapon::State S;
    S.Reset(R,120);
    assert(S.Shoot(R) && S.Magazine==29 && S.Heat==8);
    assert(!S.Shoot(R)); // repeated input cannot bypass cadence
    S.Advance(.06f,R); assert(!S.Shoot(R));
    S.Advance(.06f,R); assert(S.Shoot(R));
    assert(S.Reload(R)); assert(!S.Reload(R)); assert(!S.Shoot(R));
    S.Advance(2.21f,R); assert(S.Magazine==30 && S.Reserve==118 && !S.Reloading);
    S.Magazine=7; S.Reserve=3;
    assert(S.Reload(R)); S.Advance(3.f,R);
    assert(S.Magazine==10 && S.Reserve==0);
    assert(!S.Reload(R));
    S.Reserve=12; assert(S.Reload(R)); S.CancelReload(); S.Advance(10.f,R);
    assert(S.Magazine==10 && S.Reserve==12); // cancellation never grants rounds
    S.Reset(R,120);
    for (int i=0;i<13;++i) { assert(S.Shoot(R)); S.Advance(R.Interval,R); }
    assert(S.Overheated && S.Heat==100 && !S.Shoot(R));
    assert(S.Reload(R)); S.Advance(R.ReloadSeconds+.01f,R);
    assert(S.Overheated && !S.Shoot(R)); // reload does not reset heat
    S.Advance(10.f,R); assert(!S.Overheated && S.Heat==0 && S.Shoot(R));
    S.Magazine=0; S.FireWait=0;
    const float Heat=S.Heat;
    assert(!S.Shoot(R) && S.Heat==Heat);
    S.Reset(R,120); assert(S.Shoot(R));
    S.Advance(.4f,R); assert(std::abs(S.Heat-7.1f)<.0001f); // cool only after delay
    S.Advance(-1.f,R); assert(std::abs(S.Heat-7.1f)<.0001f);
    // Frame subdivision does not alter passive cooling or ammo transfer.
    AFWeapon::State A=S, B=S;
    A.Reload(R); B.Reload(R);
    A.Advance(3.f,R);
    for (int i=0;i<300;++i) B.Advance(.01f,R);
    assert(A.Magazine==B.Magazine && A.Reserve==B.Reserve && std::abs(A.Heat-B.Heat)<.001f);
    std::cout << "PASS: cadence, conservation, partial reload, cancellation, overheat hysteresis, cooling and empty-mag gates\n";
}
