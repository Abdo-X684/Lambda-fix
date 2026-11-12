// ---------------------------------------------------------------------
// Source: BugfixedHL-Rebased (tmp64/BugfixedHL-Rebased) @ 4d32095e...
// License: GPL-3.0-or-later. Ported INTO the OP4 client DLL with the
// bhl_compat compatibility layer (see docs/BHL_MERGE.md).
// Changes vs upstream are limited to includes/compat (marked COMPAT).
// ---------------------------------------------------------------------
#include "bhl_compat.h"  // COMPAT: BHL ConVar / constants on OP4
#include <cmath>
#include "hud.h"
#include "cl_util.h"
#include "parsemsg.h"
#include "speedometer.h"
#include <cstdio>

extern ConVar hud_jumpspeed;
extern ConVar hud_jumpspeed_below_cross;
ConVar hud_speedometer("hud_speedometer", "0", FCVAR_BHL_ARCHIVE, "Enable speedometer");
ConVar hud_speedometer_below_cross("hud_speedometer_below_cross", "0", FCVAR_BHL_ARCHIVE, "Move speedometer to below the crosshair");

DEFINE_HUD_ELEM(CHudSpeedometer);

void CHudSpeedometer::Init()
{
	m_iFlags = HUD_ACTIVE | HUD_DRAW_ALWAYS;
}

void CHudSpeedometer::VidInit()
{
}

void CHudSpeedometer::Draw(float time)
{
	// One-time diagnostic: why the speedometer/health digits may not appear.
	static bool s_bDiagPrinted = false;
	if (!s_bDiagPrinted && hud_speedometer.GetBool())
	{
		s_bDiagPrinted = true;
		int n0 = gHUD.GetSpriteIndex("number_0");
		char buf[200];
		std::snprintf(buf, sizeof(buf), "[BHL-HUD] n0=%d h0=%d sw=%d sh=%d hide=%d spectate=%d hud_draw=%g\n",
			n0, (int)gHUD.GetSprite(n0), ScreenWidth, ScreenHeight, gHUD.m_iHideHUDDisplay, gEngfuncs.IsSpectateOnly(), hud_draw.GetFloat());
		gEngfuncs.pfnConsolePrint(buf);
	}
	// TEMPORARY diagnostic (remove after testing): plain text, no sprites.
	// If this text is visible, HUD drawing works and the number sprites are the issue.
	if (hud_speedometer.GetBool())
		gEngfuncs.pfnDrawString(10, 10, "BHL-HUD TEST", 255, 255, 0);
	if ((gHUD.m_iHideHUDDisplay & HIDEHUD_HEALTH) || gEngfuncs.IsSpectateOnly())
		return;

	if (!hud_speedometer.GetBool())
		return;

	if (m_iOldSpeed != m_iSpeed)
		m_fFade = FADE_TIME;

	int r, g, b;
	float a;

	if (!hud_dim.GetBool())
		a = MIN_ALPHA + ALPHA_AMMO_MAX;
	else if (m_fFade > 0)
	{
		// Fade the number back to dim
		m_fFade -= (gHUD.m_flTimeDelta * 20);
		if (m_fFade <= 0)
			m_fFade = 0;
		a = MIN_ALPHA + (m_fFade / FADE_TIME) * ALPHA_AMMO_FLASH;
	}
	else
		a = MIN_ALPHA;

	int y;
	if (hud_speedometer_below_cross.GetBool())
	{
		y = ScreenHeight / 2 + gHUD.m_iFontHeight;
	}
	else
	{
		int yoffset = 0;

		if (hud_jumpspeed.GetBool() && !hud_jumpspeed_below_cross.GetBool())
			yoffset = gHUD.m_iFontHeight;

		y = ScreenHeight - gHUD.m_iFontHeight - gHUD.m_iFontHeight / 2 - yoffset;
	}

	if (hud_draw.GetFloat() > 0)
		a *= gHUD.GetHudTransparency();
	else
		a *= 1;
	gHUD.GetHudColor(HudPart::Common, 0, r, g, b);
	ScaleColors(r, g, b, a);
	gHUD.DrawHudNumberCentered(ScreenWidth / 2, y, m_iSpeed, r, g, b);

	m_iOldSpeed = m_iSpeed;
}

void CHudSpeedometer::UpdateSpeed(const float velocity[2])
{
	m_iSpeed = std::round(std::hypot(velocity[0], velocity[1]));
}
