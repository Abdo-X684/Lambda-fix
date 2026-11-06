/* BugfixedHL client/hud.cpp - fixture */
#include "hud.h"

void CHud::Init()
{
    HOOK_MESSAGE(Logo);
    InitVGUI2HUDElements();  /* BHL: VGUI2 HUD */
}
