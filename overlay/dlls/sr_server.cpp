// BugfixedHL x Opposing Force - Speedrun Merge Kit
// Integration glue only: compiled inside the merged OP4 server DLL.
//
// The timer never reads the renderer clock: sr::SystemClock is monotonic.
// Every level change is a split and is broadcast to clients via SRSplit, so
// the HUD shows server time rather than a client-side guess.
#include "extdll.h"
#include "util.h"
#include "cbase.h"

#include "sr_core.h"
#include "sr_server.h"

#include <cstdio>
#include <cstring>
#include <exception>

int gmsgSRSplit = 0;

namespace {
sr::SystemClock g_Clock;
sr::RunTimer g_Timer(g_Clock);
char g_LastMap[64] = {};
bool g_Valid = true;
bool g_CommandsRegistered = false;

bool CheatsEnabled() {
    return CVAR_GET_FLOAT("sv_cheats") != 0.0f;
}

int ClampToLong(sr::Ms value) {
    if (value > 2147483647LL) return 2147483647;
    if (value < -2147483648LL) return -2147483648;
    return static_cast<int>(value);
}

void BroadcastSplit(const char* map, const sr::Split& split) {
    if (gmsgSRSplit == 0 || CVAR_GET_FLOAT("sr_net_splits") == 0.0f) {
        return;
    }
    MESSAGE_BEGIN(MSG_ALL, gmsgSRSplit);
    WRITE_LONG(ClampToLong(split.at));
    WRITE_LONG(ClampToLong(split.delta));
    WRITE_BYTE(split.has_pb ? 1 : 0);
    WRITE_STRING(map);
    MESSAGE_END();
}

void SplitNow(const char* map) {
    if (!map || !map[0] || !sr::Route::IsKnownMap(map)) {
        return;
    }
    if (!g_Timer.IsRunning()) {
        return;
    }
    try {
        g_Timer.SplitAt(map);
        const sr::Split& split = g_Timer.Splits().back();
        if (CVAR_GET_FLOAT("sr_splits_announce") != 0.0f) {
            ALERT(at_console, "[BHLxOP4] split %s: %s (%c%s vs PB)\n", map,
                  sr::FormatTime(split.at).c_str(), split.delta < 0 ? '-' : '+',
                  sr::FormatTime(split.delta < 0 ? -split.delta : split.delta).c_str());
        }
        BroadcastSplit(map, split);
    } catch (const std::exception&) {
        // Skipping backwards in the route (practice) must not crash a run.
    }
}

void Command_Split() { SplitNow(g_LastMap); }

void Command_Reset() {
    SR_Server_Reset();
    g_Timer.Start();
    ALERT(at_console, "[BHLxOP4] run reset\n");
}

void Command_Practice() {
    const float current = CVAR_GET_FLOAT("sr_practice_mode");
    CVAR_SET_FLOAT("sr_practice_mode", current != 0.0f ? 0.0f : 1.0f);
    ALERT(at_console, "[BHLxOP4] practice mode %s\n",
          current != 0.0f ? "off" : "on (PB writes disabled)");
}

void RegisterCommands() {
    if (g_CommandsRegistered) {
        return;
    }
    g_engfuncs.pfnAddServerCommand("sr_split", Command_Split);
    g_engfuncs.pfnAddServerCommand("sr_reset", Command_Reset);
    g_engfuncs.pfnAddServerCommand("sr_practice_toggle", Command_Practice);
    g_CommandsRegistered = true;
}
}  // namespace

void SR_Server_OnMapSpawn(const char* map) {
    RegisterCommands();
    // Fallback for builds where UserMessages.cpp was not patched.
    if (gmsgSRSplit == 0) {
        gmsgSRSplit = REG_USER_MSG("SRSplit", -1);
    }
    if (!map || !map[0]) {
        return;
    }
    if (CheatsEnabled()) {
        g_Valid = false;
        ALERT(at_console, "[BHLxOP4] sv_cheats is on - this run is INVALID\n");
    }
    if (!g_Timer.IsRunning() && !g_Timer.IsFinished()) {
        g_Timer.Start();
    }
    if (std::strcmp(g_LastMap, map) == 0) {
        return;  // save/load reload of the same map: no duplicate split
    }
    std::snprintf(g_LastMap, sizeof(g_LastMap), "%s", map);
    SplitNow(map);
}

void SR_Server_OnClientPutInServer(edict_t* pEntity) {
    (void)pEntity;
    if (CheatsEnabled()) {
        g_Valid = false;
    }
    ALERT(at_console, "[BHLxOP4] timer ready - sv_cheats=%s, run %s\n",
          CheatsEnabled() ? "ON (invalid)" : "0",
          SR_Server_RunIsValid() ? "valid" : "invalid");
}

void SR_Server_Split() { SplitNow(g_LastMap); }

void SR_Server_Reset() {
    g_Timer.Reset();
    g_LastMap[0] = '\0';
    g_Valid = !CheatsEnabled();
}

bool SR_Server_RunIsValid() {
    return g_Valid && !CheatsEnabled() &&
           CVAR_GET_FLOAT("sr_practice_mode") == 0.0f;
}
