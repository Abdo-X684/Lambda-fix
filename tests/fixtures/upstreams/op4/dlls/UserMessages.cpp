/* OP4 UserMessages.cpp - fixture */
#include "UserMessages.h"

void LinkUserMessages()
{
	gmsgInitHUD = REG_USER_MSG("InitHUD", 0);
	gmsgShowGameTitle = REG_USER_MSG("GameTitle", 1);
	gmsgDeathMsg = REG_USER_MSG("DeathMsg", -1);
}
