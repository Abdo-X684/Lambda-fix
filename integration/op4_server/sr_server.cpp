// BugfixedHL x Opposing Force - Speedrun Merge Kit
// Integration glue only: compiled inside the merged OP4 server DLL.
//
// The timer never reads the renderer clock: sr::SystemClock is monotonic.
// Every level change is a split and is broadcast to clients via SRSplit, so
// the HUD shows server time rather than a client-side guess.
//
// v0.1.1: register the sr_* cvars on the server as well (an unregistered cvar
// reads back as 0, which used to suppress every split broadcast and every
// console announce), print a loud load banner and add `sr_status` so it is
// trivial to confirm that THIS hl.so is loaded.
#include "extdll.h"
#include "util.h"
#include "cbase.h"

#include "sr_core.h"
#include "sr_server.h"

#include <cstdio>
#include <cstring>
#include <exception>

#define SR_KIT_VERSION "0.1.1"

int gmsgSRSplit = 0;

// GoldSrc compiles with -fno-exceptions; keep the guard on the host and make
// it a no-op branch inside the engine.
#if defined(__cpp_exceptions) || defined(__EXCEPTIONS) || defined(_CPPUNWIND)
#define SR_TRY try
#define SR_CATCH_ALL catch (const std::exception&)
#else
#define SR_TRY if (true)
#define SR_CATCH_ALL if (false)
#endif

namespace {
sr::SystemClock g_Clock;
sr::RunTimer g_Timer(g_Clock);
char g_LastMap[64] = {};
bool g_Valid = true;
bool g_CommandsRegistered = false;
bool g_Announced = false;

// Registered with CVAR_REGISTER below; without this, CVAR_GET_FLOAT() on an
// unknown cvar returns 0 even when speedrun.cfg set it to 1.
cvar_t sr_cv_net_splits = {"sr_net_splits", "1", FCVAR_SERVER};
cvar_t sr_cv_splits_announce = {"sr_splits_announce", "1", FCVAR_SERVER};
cvar_t sr_cv_practice_mode = {"sr_practice_mode", "0", FCVAR_SERVER};
cvar_t sr_cv_version = {"sr_version", SR_KIT_VERSION, FCVAR_SERVER};

float SrCvar(const char* name, float fallback) {
    const float value = CVAR_GET_FLOAT(name);
    // An unregistered cvar is indistinguishable from "set to 0", so fall back
    // to the built-in default when the engine knows nothing about it.
    return value == 0.0f ? fallback : value;
}

bool CheatsEnabled() {
    return CVAR_GET_FLOAT("sv_cheats") != 0.0f;
}

int ClampToLong(sr::Ms value) {
    if (value > 2147483647LL) return 2147483647;
    if (value < -2147483648LL) return -2147483648;
    return static_cast<int>(value);
}

void BroadcastSplit(const char* map, const sr::Split& split) {
    if (gmsgSRSplit == 0 || SrCvar("sr_net_splits", 1.0f) == 0.0f) {
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
    SR_TRY {
        g_Timer.SplitAt(map);
        const sr::Split& split = g_Timer.Splits().back();
        if (SrCvar("sr_splits_announce", 1.0f) != 0.0f) {
            ALERT(at_console, "[BHLxOP4] split %s: %s (%c%s vs PB)\n", map,
                  sr::FormatTime(split.at).c_str(), split.delta < 0 ? '-' : '+',
                  sr::FormatTime(split.delta < 0 ? -split.delta : split.delta).c_str());
        }
        BroadcastSplit(map, split);
    } SR_CATCH_ALL {
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
    const float current = SrCvar("sr_practice_mode", 0.0f);
    CVAR_SET_FLOAT("sr_practice_mode", current != 0.0f ? 0.0f : 1.0f);
    ALERT(at_console, "[BHLxOP4] practice mode %s\n",
          current != 0.0f ? "off" : "on (PB writes disabled)");
}

void Command_Status() {
    ALERT(at_console, "\n[BHLxOP4] ============================================\n");
    ALERT(at_console, "[BHLxOP4]  BugfixedHL x OP4 Speedrun v" SR_KIT_VERSION "\n");
    ALERT(at_console, "[BHLxOP4]  hl.so LOADED - merge is active\n");
    ALERT(at_console, "[BHLxOP4]  map=%s  timer=%s  run=%s  elapsed=%s\n",
          g_LastMap[0] ? g_LastMap : "(none)",
          g_Timer.IsRunning() ? "running" : "stopped",
          SR_Server_RunIsValid() ? "valid" : "invalid",
          sr::FormatTime(g_Timer.ElapsedMs()).c_str());
    ALERT(at_console, "[BHLxOP4]  sv_cheats=%s  sr_net_splits=%.0f  sr_practice_mode=%.0f\n",
          CheatsEnabled() ? "ON (invalid)" : "0",
          CVAR_GET_FLOAT("sr_net_splits"), CVAR_GET_FLOAT("sr_practice_mode"));
    ALERT(at_console, "[BHLxOP4]  route: 39 maps / 13 chapter splits\n");
    ALERT(at_console, "[BHLxOP4]  commands: sr_split sr_reset sr_practice_toggle sr_status\n");
    ALERT(at_console, "[BHLxOP4] ============================================\n\n");
}

void RegisterCommands() {
    if (g_CommandsRegistered) {
        return;
    }
    CVAR_REGISTER(&sr_cv_net_splits);
    CVAR_REGISTER(&sr_cv_splits_announce);
    CVAR_REGISTER(&sr_cv_practice_mode);
    CVAR_REGISTER(&sr_cv_version);
    g_engfuncs.pfnAddServerCommand("sr_split", Command_Split);
    g_engfuncs.pfnAddServerCommand("sr_reset", Command_Reset);
    g_engfuncs.pfnAddServerCommand("sr_practice_toggle", Command_Practice);
    g_engfuncs.pfnAddServerCommand("sr_status", Command_Status);
    g_CommandsRegistered = true;
}
}  // namespace

void SR_Server_OnMapSpawn(const char* map) {
    RegisterCommands();
    // Fallback for builds where UserMessages.cpp was not patched.
    if (gmsgSRSplit == 0) {
        gmsgSRSplit = REG_USER_MSG("SRSplit", -1);
    }
    if (!g_Announced) {
        ALERT(at_console, "\n[BHLxOP4] ============================================\n");
        ALERT(at_console, "[BHLxOP4]  BugfixedHL x OP4 Speedrun v" SR_KIT_VERSION "\n");
        ALERT(at_console, "[BHLxOP4]  server DLL LOADED - type sr_status in console\n");
        ALERT(at_console, "[BHLxOP4] ============================================\n\n");
        g_Announced = true;
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
