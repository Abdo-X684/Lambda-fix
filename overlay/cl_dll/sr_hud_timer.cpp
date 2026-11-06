// BugfixedHL x Opposing Force - Speedrun Merge Kit
// Integration glue only: compiled inside the merged OP4 client DLL.
#include "hud.h"
#include "cl_util.h"

#include "sr_core.h"
#include "sr_hud_timer.h"

#include <cstdio>
#include <ctime>
#include <exception>
#include <string>

namespace {
sr::SystemClock g_Clock;
sr::ServerMirror g_Mirror;
sr::RunTimer g_Timer(g_Clock);
char g_LastSplit[64] = {};
sr::Ms g_LastDelta = 0;
bool g_HasDelta = false;
bool g_Enabled = true;
bool g_DemoOn = false;

void RestartDemo() {
    if (!g_DemoOn) {
        return;
    }
    EngineClientCmd("stop");
    char name[128];
    std::snprintf(name, sizeof(name), "record sr_run_%lld",
                  static_cast<long long>(std::time(nullptr)));
    EngineClientCmd(name);
}
}  // namespace

void SR_HUD_Init() {
    g_Mirror.Reset();
    g_Timer.Reset();
    g_LastSplit[0] = '\0';
    g_HasDelta = false;
    g_Enabled = CVAR_GET_FLOAT("sr_timer_enable") != 0.0f &&
                CVAR_GET_FLOAT("sr_timer_hud") != 0.0f;
    g_DemoOn = CVAR_GET_FLOAT("sr_autodemo") != 0.0f;
    RestartDemo();
}

void SR_HUD_Reset() {
    g_Mirror.Reset();
    g_Timer.Reset();
    g_LastSplit[0] = '\0';
    g_HasDelta = false;
    RestartDemo();
}

void SR_HUD_OnSplit(const char* map, sr::Ms at, sr::Ms delta, bool hasPb) {
    if (!map) {
        return;
    }
    const std::string mapName(map);
    const bool finished = mapName == sr::Route::LastMap();
    // Authoritative time replaces any local fallback from this point on.
    g_Mirror.OnServerSplit(at, g_Clock.NowMs(), finished);
    std::snprintf(g_LastSplit, sizeof(g_LastSplit), "%s", map);
    g_LastDelta = delta;
    g_HasDelta = hasPb;
    if (finished) {
        EngineClientCmd("stop");
    }
}

void SR_HUD_Redraw(float flTime) {
    (void)flTime;
    if (!g_Enabled) {
        return;
    }
    const sr::Ms shown = g_Mirror.HasServer()
                             ? g_Mirror.ProjectedMs(g_Clock.NowMs())
                             : g_Timer.ElapsedMs();
    if (shown <= 0 && !g_Mirror.HasServer() && !g_Timer.IsRunning()) {
        return;
    }
    const int x = static_cast<int>(gHUD.m_scrinfo.iWidth * 0.04f);
    const int y = static_cast<int>(gHUD.m_scrinfo.iHeight * 0.04f);
    char line[160];
    std::snprintf(line, sizeof(line), "RTA  %s", sr::FormatTime(shown).c_str());
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
