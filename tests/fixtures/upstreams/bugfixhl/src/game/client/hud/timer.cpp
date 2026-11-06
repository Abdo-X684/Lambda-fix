/* BugfixedHL HUD timer - fixture (GPL-3.0 reference only) */
#include "hud/timer.h"
#include "src/common/convar.h"

void CHudTimer::Init() { m_flStart = 0.0f; }
void CHudTimer::Draw(float flTime) { /* upstream timer drawing */ }
