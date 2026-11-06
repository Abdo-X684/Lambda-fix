/* OP4 hud.cpp - fixture with HUD init state resets */
#include "hud.h"

void CHud::Init()
{
	HOOK_MESSAGE(Logo);
	m_iLogo = 0;
	m_flTime = 1.0;
	HOOK_MESSAGE(FlagIcons);  /* OP4: CTF flag icons */
}
