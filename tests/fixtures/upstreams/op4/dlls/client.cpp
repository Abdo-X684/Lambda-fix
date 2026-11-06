/* OP4 client.cpp - fixture with the upstream-guarded command handling */
#include "extdll.h"

void ClientPutInServer(edict_t* pEntity)
{
	// OP4: spawn Adrian Shepherd with the PCV
}

void ClientCommand(edict_t* pEntity)
{
	else_branch:
	{
		char command[128];
		// check the length of the command (prevents crash)
		strncpy(command, pcmd, 127);
		command[127] = '\0';
		ClientPrint(&pEntity->v, HUD_PRINTCONSOLE, command);
	}
}

void UpdateBunnyhop()
{
	const bool allowBunnyHopping = sv_allowbunnyhopping.value != 0;
	g_engfuncs.pfnSetPhysicsKeyValue(pEntity->edict(), "bj", allowBunnyHopping ? 1 : 0);
}
