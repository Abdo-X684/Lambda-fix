// ---------------------------------------------------------------------
// Source: BugfixedHL-Rebased (tmp64/BugfixedHL-Rebased) @ 4d32095e...
// License: GPL-3.0-or-later. Ported to OP4 VGUI1 (FillRGBA instead of
// vgui2 surface). Settings: cl_cross_* (see crosshair.cpp).
// ---------------------------------------------------------------------
#ifndef HUD_CROSSHAIR_H
#define HUD_CROSSHAIR_H
#include "base.h"

class CHudCrosshair : public CHudElemBase<CHudCrosshair>
{
public:
	CHudCrosshair();
	virtual void Init();
	virtual void Draw(float flTime);
	bool IsEnabled();
};

#endif
