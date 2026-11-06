// ---------------------------------------------------------------------
// Source: BugfixedHL-Rebased src/game/server/CBugfixedServer.cpp
// (GPL-3.0-or-later), lines declaring the sv_bhl_* cvars.
//
// Ported INTO the OP4 server DLL. COMPAT changes only: BHL's ConVar +
// IBugfixedServer/EXPOSE_SINGLE_INTERFACE machinery is replaced by OP4's
// native cvar_t/CVAR_REGISTER, and Init() also prints a load banner.
// The cvars themselves, their names, defaults and descriptions are BHL's.
// ---------------------------------------------------------------------
#include "extdll.h"
#include "util.h"
#include "cbase.h"

#include "bhl_server.h"

static cvar_t sv_bhl_query_vars = {
    "sv_bhl_query_vars", "0", FCVAR_SERVER
};
static cvar_t sv_bhl_query_wait_for_id = {
    "sv_bhl_query_wait_for_id", "0", FCVAR_SERVER
};
static cvar_t sv_bhl_defer_motd = {
    "sv_bhl_defer_motd", "0", FCVAR_SERVER
};
static cvar_t sv_bhl_version = {
    "sv_bhl_version", "bhl-systems-1", FCVAR_SERVER
};

void BHL_Server_Init()
{
    static bool s_Registered = false;
    if (s_Registered)
        return;
    s_Registered = true;

    CVAR_REGISTER(&sv_bhl_query_vars);
    CVAR_REGISTER(&sv_bhl_query_wait_for_id);
    CVAR_REGISTER(&sv_bhl_defer_motd);
    CVAR_REGISTER(&sv_bhl_version);

    ALERT(at_console, "\n[BHL] ================================================\n");
    ALERT(at_console, "[BHL]  BugfixedHL server systems merged into OP4\n");
    ALERT(at_console, "[BHL]  sv_bhl_query_vars / sv_bhl_query_wait_for_id\n");
    ALERT(at_console, "[BHL]  sv_bhl_defer_motd / sv_bhl_version\n");
    ALERT(at_console, "[BHL] ================================================\n\n");
}
