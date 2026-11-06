// BugfixedHL x Opposing Force - Speedrun Merge Kit
// Thin client-side HUD mirror. The authoritative timer lives on the server
// (dlls/sr_server.cpp); this mirror keeps the HUD usable in single player and
// receives split updates through SR_HUD_OnSplit.
#pragma once

#include "sr_core.h"

void SR_HUD_Init();
void SR_HUD_Redraw(float flTime);
void SR_HUD_OnSplit(const char* map, sr::Ms at, sr::Ms delta, bool hasPb);
void SR_HUD_Reset();
