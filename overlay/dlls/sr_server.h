// BugfixedHL x Opposing Force - Speedrun Merge Kit
// Server-authoritative RTA run timer for the merged OP4 server DLL.
#pragma once

#include "extdll.h"
#include "sr_core.h"

void SR_Server_OnMapSpawn(const char* map);
void SR_Server_OnClientPutInServer(edict_t* pEntity);
void SR_Server_Split();
void SR_Server_Reset();
bool SR_Server_RunIsValid();
