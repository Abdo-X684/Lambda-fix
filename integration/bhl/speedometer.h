// ---------------------------------------------------------------------
// Source: BugfixedHL-Rebased (tmp64/BugfixedHL-Rebased) @ 4d32095e...
// License: GPL-3.0-or-later. Ported INTO the OP4 client DLL with the
// bhl_compat compatibility layer (see docs/BHL_MERGE.md).
// Changes vs upstream are limited to includes/compat (marked COMPAT).
// ---------------------------------------------------------------------
#ifndef HUD_SPEEDOMETER_H
#define HUD_SPEEDOMETER_H
#include "base.h"

class CHudSpeedometer : public CHudElemBase<CHudSpeedometer>
{
public:
	virtual void Init();
	virtual void VidInit();
	virtual void Draw(float time);
	void UpdateSpeed(const float velocity[2]);

private:
	int m_iOldSpeed;
	int m_iSpeed;
	float m_fFade;
};

#endif
