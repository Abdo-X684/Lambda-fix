// ---------------------------------------------------------------------
// Source: BugfixedHL-Rebased (tmp64/BugfixedHL-Rebased) @ 4d32095e...
// License: GPL-3.0-or-later. Ported to OP4 VGUI1: the crosshair is drawn
// with gEngfuncs.pfnFillRGBA (no vgui2 surface). Logic follows BHL's
// CCrosshairImage::Paint.
// ---------------------------------------------------------------------
#include <cmath>
#include "hud.h"
#include "cl_util.h"
#include "crosshair.h"

ConVar cl_cross_enable("cl_cross_enable", "1", FCVAR_BHL_ARCHIVE, "Draw the custom crosshair");
ConVar cl_cross_red("cl_cross_red", "0", FCVAR_BHL_ARCHIVE, "Crosshair red");
ConVar cl_cross_green("cl_cross_green", "255", FCVAR_BHL_ARCHIVE, "Crosshair green");
ConVar cl_cross_blue("cl_cross_blue", "255", FCVAR_BHL_ARCHIVE, "Crosshair blue");
ConVar cl_cross_gap("cl_cross_gap", "4", FCVAR_BHL_ARCHIVE, "Crosshair gap");
ConVar cl_cross_size("cl_cross_size", "6", FCVAR_BHL_ARCHIVE, "Crosshair arm length");
ConVar cl_cross_thickness("cl_cross_thickness", "2", FCVAR_BHL_ARCHIVE, "Crosshair thickness");
ConVar cl_cross_outline_thickness("cl_cross_outline_thickness", "0", FCVAR_BHL_ARCHIVE, "Crosshair outline");
ConVar cl_cross_dot("cl_cross_dot", "0", FCVAR_BHL_ARCHIVE, "Draw centre dot");
ConVar cl_cross_t("cl_cross_t", "0", FCVAR_BHL_ARCHIVE, "T-shaped crosshair");
ConVar cl_cross_zoom("cl_cross_zoom", "2", FCVAR_BHL_ARCHIVE, "Zoomed crosshair mode: sprite, custom, both");

namespace {

struct XhSettings
{
	int r, g, b;
	int gap, thickness, outline, size;
	bool dot, t;
};

void FillRect(int x0, int y0, int x1, int y1, int r, int g, int b)
{
	int left = x0 < x1 ? x0 : x1;
	int right = x0 < x1 ? x1 : x0;
	int top = y0 < y1 ? y0 : y1;
	int bottom = y0 < y1 ? y1 : y0;
	gEngfuncs.pfnFillRGBA(left, top, right - left, bottom - top, r, g, b, 255);
}

void DrawVLine(int x0, int y0, int len, int thick, int r, int g, int b)
{
	int htp = (int)std::floor(thick / 2.0f);
	int htn = (int)std::floor(-thick / 2.0f);
	FillRect(x0 + htn, y0, x0 + htp + 1, y0 + len, r, g, b);
}

void DrawHLine(int x0, int y0, int len, int thick, int r, int g, int b)
{
	int htp = (int)std::floor(thick / 2.0f);
	int htn = (int)std::floor(-thick / 2.0f);
	FillRect(x0, y0 + htn, x0 + len, y0 + htp + 1, r, g, b);
}

void DrawDot(int x, int y, int size, int r, int g, int b)
{
	int hp = (int)std::floor(+size / 2.0f);
	int hn = (int)std::floor(-size / 2.0f);
	FillRect(x + hn, y + hn, x + hp + 1, y + hp + 1, r, g, b);
}

void PaintCrosshair(int cx, int cy, const XhSettings& s)
{
	int gap = s.gap;
	int thick = s.thickness;
	// Gap must match the thickness parity, otherwise the lines misalign.
	if (thick % 2 == 0)
		gap = gap * 2;
	else
		gap = gap * 2 + 1;

	int halfGapPos = (int)std::floor(gap / 2.0f);
	int halfGapNeg = (int)std::floor(-gap / 2.0f);

	if (s.outline > 0)
	{
		int olSize = s.size + 2 * s.outline;
		int olThick = thick + 2 * s.outline;
		int olHalfGapPos = halfGapPos - s.outline;
		int olHalfGapNeg = halfGapNeg + s.outline;
		if (!s.t)
			DrawVLine(cx, cy + olHalfGapNeg, -olSize, olThick, 0, 0, 0);
		DrawVLine(cx, cy + olHalfGapPos, +olSize, olThick, 0, 0, 0);
		DrawHLine(cx + olHalfGapNeg, cy, -olSize, olThick, 0, 0, 0);
		DrawHLine(cx + olHalfGapPos, cy, +olSize, olThick, 0, 0, 0);
		if (s.dot)
			DrawDot(cx, cy, olThick, 0, 0, 0);
	}

	if (s.dot)
		DrawDot(cx, cy, thick, s.r, s.g, s.b);
	if (!s.t)
		DrawVLine(cx, cy + halfGapNeg, -s.size, thick, s.r, s.g, s.b);
	DrawVLine(cx, cy + halfGapPos, +s.size, thick, s.r, s.g, s.b);
	DrawHLine(cx + halfGapNeg, cy, -s.size, thick, s.r, s.g, s.b);
	DrawHLine(cx + halfGapPos, cy, +s.size, thick, s.r, s.g, s.b);
}

} // namespace

DEFINE_HUD_ELEM(CHudCrosshair);

CHudCrosshair::CHudCrosshair()
{
}

void CHudCrosshair::Init()
{
	m_iFlags |= HUD_ACTIVE | HUD_DRAW_ALWAYS;
}

void CHudCrosshair::Draw(float flTime)
{
	if (gHUD.m_iHideHUDDisplay & HIDEHUD_ALL)
		return;
	if (!cl_cross_enable.GetBool())
		return;

	// Zoomed view: follow cl_cross_zoom (0 = never, 1 = sprite, 2 = custom, both allowed)
	bool isZoomed = gHUD.m_iFOV < 90;
	int zoomMode = cl_cross_zoom.GetInt();
	if (isZoomed && !(zoomMode == 1 || zoomMode == 2))
		return;

	XhSettings s;
	s.r = cl_cross_red.GetInt();
	s.g = cl_cross_green.GetInt();
	s.b = cl_cross_blue.GetInt();
	s.gap = cl_cross_gap.GetInt();
	s.thickness = cl_cross_thickness.GetInt();
	s.outline = cl_cross_outline_thickness.GetInt();
	s.size = cl_cross_size.GetInt();
	s.dot = cl_cross_dot.GetBool();
	s.t = cl_cross_t.GetBool();

	PaintCrosshair(ScreenWidth / 2, ScreenHeight / 2, s);
}

bool CHudCrosshair::IsEnabled()
{
	return cl_cross_enable.GetBool();
}
