/* OP4 hud_redraw.cpp - fixture */
#include "hud.h"

#define MAX_LOGO_FRAMES 56

bool CHud::Redraw(float flTime, bool intermission)
{
	m_fOldTime = m_flTime;
	return true;
}
