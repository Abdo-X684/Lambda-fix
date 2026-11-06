// BugfixedHL x Opposing Force - Speedrun Merge Kit
// Integration glue only: compiled inside the merged OP4 client DLL.
//
// v0.1.1: the HUD used to be invisible on a fresh map. Two reasons:
//   1. none of the sr_* cvars were registered on the client, so
//      CVAR_GET_FLOAT("sr_timer_enable") returned 0 unless speedrun.cfg had
//      been exec'd before the DLL loaded;
//   2. the local RunTimer was never started, and SR_HUD_Redraw() returned
//      early while shown == 0 with no server split yet.
// Now every cvar is registered with a visible default, the local timer starts
// at CHud::Init(), and an unmistakable green brand banner is drawn from the
// very first frame. It is also the quickest way to tell whether THIS client.so
// is actually loaded.
#include "hud.h"
#include "cl_util.h"

#include "sr_core.h"
#include "sr_hud_timer.h"

#include <cstdio>
#include <ctime>
#include <string>

#define SR_KIT_VERSION "0.1.1"

namespace {
sr::SystemClock g_Clock;
sr::ServerMirror g_Mirror;
sr::RunTimer g_Timer(g_Clock);
char g_LastSplit[64] = {};
sr::Ms g_LastDelta = 0;
bool g_HasDelta = false;
bool g_DemoOn = false;
bool g_Announced = false;

cvar_t* g_pEnable = nullptr;
cvar_t* g_pHud = nullptr;
cvar_t* g_pBanner = nullptr;
cvar_t* g_pDemo = nullptr;

bool SrOn(cvar_t* var, float fallback) {
    return (var ? var->value : fallback) != 0.0f;
}

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
    // Register on the client. An unregistered cvar reads back as 0.0, which
    // silently disabled the whole overlay for anyone who did not pass
    // "+exec speedrun.cfg" on the command line.
    g_pEnable = CVAR_CREATE("sr_timer_enable", "1", FCVAR_ARCHIVE);
    g_pHud = CVAR_CREATE("sr_timer_hud", "1", FCVAR_ARCHIVE);
    g_pBanner = CVAR_CREATE("sr_hud_banner", "1", FCVAR_ARCHIVE);
    g_pDemo = CVAR_CREATE("sr_autodemo", "1", FCVAR_ARCHIVE);
    CVAR_CREATE("sr_timer_hud_pos", "0.82 0.04", FCVAR_ARCHIVE);
    CVAR_CREATE("sr_pb_path", "splits/op4_pb.txt", FCVAR_ARCHIVE);

    g_Mirror.Reset();
    g_Timer.Reset();
    g_Timer.Start();  // local fallback: time is visible from the first frame
    g_LastSplit[0] = '\0';
    g_HasDelta = false;
    g_DemoOn = SrOn(g_pDemo, 1.0f);

    if (!g_Announced) {
        ConsolePrint("\n[BHLxOP4] ============================================\n");
        ConsolePrint("[BHLxOP4]  BugfixedHL x OP4 Speedrun v" SR_KIT_VERSION "\n");
        ConsolePrint("[BHLxOP4]  client.so LOADED - HUD banner is ON\n");
        ConsolePrint("[BHLxOP4]  sr_status (server) / sr_hud_banner 0|1\n");
        ConsolePrint("[BHLxOP4] ============================================\n\n");
        g_Announced = true;
    }
    // Deliberately no RestartDemo() here: issuing engine commands from
    // CHud::Init() is too early. Recording starts on the first reset/split.
}

void SR_HUD_Reset() {
    g_Mirror.Reset();
    g_Timer.Reset();
    g_Timer.Start();
    g_LastSplit[0] = '\0';
    g_HasDelta = false;
    g_DemoOn = SrOn(g_pDemo, 1.0f);
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
    const bool enabled = SrOn(g_pEnable, 1.0f) && SrOn(g_pHud, 1.0f);
    const bool banner = SrOn(g_pBanner, 1.0f);
    if (!enabled && !banner) {
        return;
    }
    if (gHUD.m_scrinfo.iWidth <= 0 || gHUD.m_scrinfo.iHeight <= 0) {
        return;
    }

    const int lh = gHUD.m_scrinfo.iCharHeight > 0 ? gHUD.m_scrinfo.iCharHeight : 12;
    const int x = static_cast<int>(gHUD.m_scrinfo.iWidth * 0.04f);
    int y = static_cast<int>(gHUD.m_scrinfo.iHeight * 0.04f);

    if (banner) {
        // Green brand line: a zero-effort visual check that our DLL is loaded.
        gEngfuncs.pfnDrawSetTextColor(0.25f, 1.0f, 0.55f);
        DrawConsoleString(x, y, "[ BHL x OP4 SPEEDRUN ]  v" SR_KIT_VERSION);
        y += lh;
    }

    if (enabled) {
        gEngfuncs.pfnDrawSetTextColor(1.0f, 1.0f, 1.0f);
        const sr::Ms shown = g_Mirror.HasServer()
                                 ? g_Mirror.ProjectedMs(g_Clock.NowMs())
                                 : g_Timer.ElapsedMs();
        char line[160];
        std::snprintf(line, sizeof(line), "RTA  %s", sr::FormatTime(shown).c_str());
        DrawConsoleString(x, y, line);
        y += lh;

        char split[160];
        if (g_LastSplit[0] != '\0') {
            if (g_HasDelta) {
                const char sign = g_LastDelta < 0 ? '-' : '+';
                const sr::Ms absDelta = g_LastDelta < 0 ? -g_LastDelta : g_LastDelta;
                std::snprintf(split, sizeof(split), "%s  %c%s", g_LastSplit, sign,
                              sr::FormatTime(absDelta).c_str());
            } else {
                std::snprintf(split, sizeof(split), "%s  --:--.---", g_LastSplit);
            }
        } else {
            std::snprintf(split, sizeof(split), "SPLIT  waiting for first map change");
        }
        DrawConsoleString(x, y, split);
    }
    // Restore the engine's default text colour for the rest of the HUD.
    gEngfuncs.pfnDrawSetTextColor(1.0f, 1.0f, 1.0f);
}
