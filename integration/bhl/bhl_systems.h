// ---------------------------------------------------------------------
// Source: BugfixedHL-Rebased (tmp64/BugfixedHL-Rebased) @ 4d32095e...
// License: GPL-3.0-or-later. Ported INTO the OP4 client DLL with the
// bhl_compat compatibility layer (see docs/BHL_MERGE.md).
// Changes vs upstream are limited to includes/compat (marked COMPAT).
// ---------------------------------------------------------------------
// BugfixedHL -> Opposing Force: lifecycle hooks for the MERGED BHL systems.
// Injected into OP4's hud.cpp / hud_redraw.cpp / view.cpp / input.cpp and
// dlls/world.cpp by merge/bhl.py. This header deliberately stays tiny so the
// OP4 files do not need the whole BHL compatibility layer.
#ifndef BHL_SYSTEMS_H
#define BHL_SYSTEMS_H

struct ref_params_s;

void BHL_Init();
void BHLX_Init();  // bhlx_menu console command (bhlx_menu.cpp)
void BHL_OnDeathMsg(int killer, int victim);  // cl_killsound (death.cpp injection)
void BHL_VidInit();
void BHL_Draw(float flTime);
void BHL_Think();
void BHL_OnRefdef(struct ref_params_s* pparams);
void BHL_Shutdown();

void BHL_Server_Init();

#endif  // BHL_SYSTEMS_H
