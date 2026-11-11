// BugfixedHL -> Opposing Force: lifecycle hooks for the MERGED BHL systems.
// Injected into OP4's hud.cpp / hud_redraw.cpp / view.cpp / input.cpp and
// dlls/world.cpp by merge/bhl.py. This header deliberately stays tiny so the
// OP4 files do not need the whole BHL compatibility layer.
#ifndef BHL_SYSTEMS_H
#define BHL_SYSTEMS_H

struct ref_params_s;

void BHL_Init();
void BHL_VidInit();
void BHL_Draw(float flTime);
void BHL_Think();
void BHL_OnRefdef(struct ref_params_s* pparams);
void BHL_Shutdown();

void BHL_Server_Init();

#endif  // BHL_SYSTEMS_H
