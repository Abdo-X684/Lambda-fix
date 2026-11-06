// BugfixedHL x Opposing Force - Speedrun Merge Kit
// Timer HUD. Time comes from the server (SRSplit user message); the local
// RunTimer is only a fallback when no server message has arrived.
#pragma once

#include "sr_core.h"

void SR_HUD_Init();
void SR_HUD_Redraw(float flTime);
void SR_HUD_OnSplit(const char* map, sr::Ms at, sr::Ms delta, bool hasPb);
void SR_HUD_Reset();
