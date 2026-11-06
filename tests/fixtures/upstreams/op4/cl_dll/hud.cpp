/* OP4 hud.cpp - fixture */
#include "hud.h"

void CHud::Init()
{
    HOOK_MESSAGE(Logo);
    HOOK_MESSAGE(FlagIcons);  /* OP4: CTF flag icons */
}
