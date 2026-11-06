// BugfixedHL x Opposing Force - Speedrun Merge Kit
// Integration glue only: compiled inside the merged OP4 client DLL.
#include "hud.h"
#include "cl_util.h"

#include "sr_core.h"
#include "sr_hud_timer.h"

#include <cstdio>
#include <exception>
#include <string>

namespace {
sr::SystemClock g_Clock;
sr::RunTimer g_Timer(g_Clock);
char g_LastSplit[64] = {};
sr::Ms g_LastDelta = 0;
bool g_HasDelta = false;
bool g_Enabled = true;
}  // namespace

void SR_HUD_Init() {
    g_Timer.Reset();
    g_LastSplit[0] = '\0';
    g_HasDelta = false;
    // Follow the cvar without hard-failing when it does not exist yet.
    g_Enabled = CVAR_GET_FLOAT("sr_timer_enable") != 0.0f &&
                CVAR_GET_FLOAT("sr_timer_hud") != 0.0f;
}

void SR_HUD_Reset() {
    g_Timer.Reset();
    g_LastSplit[0] = '\0';
    g_HasDelta = false;
}

void SR_HUD_OnSplit(const char* map, sr::Ms at, sr::Ms delta, bool hasPb) {
    if (!map) {
        return;
    }
    std::snprintf(g_LastSplit, sizeof(g_LastSplit), "%s", map);
    g_LastDelta = delta;
    g_HasDelta = hasPb;
    if (!g_Timer.IsRunning() && !g_Timer.IsFinished()) {
        g_Timer.Start();
    }
    if (g_Timer.IsRunning() && sr::Route::IsKnownMap(map)) {
        try {
            g_Timer.SplitAt(map);
        } catch (const std::exception&) {
            // Out-of-order map (practice / custom map): keep the HUD alive.
        }
    }
    (void)at;
}

void SR_HUD_Redraw(float flTime) {
    (void)flTime;
    if (!g_Enabled || (!g_Timer.IsRunning() && !g_Timer.IsFinished())) {
        return;
    }
    const int x = static_cast<int>(gHUD.m_scrinfo.iWidth * 0.04f);
    const int y = static_cast<int>(gHUD.m_scrinfo.iHeight * 0.04f);
    const std::string total = sr::FormatTime(g_Timer.ElapsedMs());
    char line[160];
    std::snprintf(line, sizeof(line), "RTA  %s", total.c_str());
    DrawConsoleString(x, y, line);

    if (g_LastSplit[0] != '\0') {
        char split[160];
        if (g_HasDelta) {
            const char sign = g_LastDelta < 0 ? '-' : '+';
            const sr::Ms absDelta = g_LastDelta < 0 ? -g_LastDelta : g_LastDelta;
            std::snprintf(split, sizeof(split), "%s  %c%s", g_LastSplit, sign,
                          sr::FormatTime(absDelta).c_str());
        } else {
            std::snprintf(split, sizeof(split), "%s  --:--.---", g_LastSplit);
        }
        DrawConsoleString(x, y + gHUD.m_scrinfo.iCharHeight, split);
    }
}
