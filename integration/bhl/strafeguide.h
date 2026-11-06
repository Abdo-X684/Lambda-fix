// ---------------------------------------------------------------------
// Source: BugfixedHL-Rebased (tmp64/BugfixedHL-Rebased) @ 4d32095e...
// License: GPL-3.0-or-later. Ported INTO the OP4 client DLL with the
// bhl_compat compatibility layer (see docs/BHL_MERGE.md).
// Changes vs upstream are limited to includes/compat (marked COMPAT).
// ---------------------------------------------------------------------
#ifndef HUD_STRAFEGUIDE_H
#define HUD_STRAFEGUIDE_H
#include "base.h"
#include <complex>

class CHudStrafeGuide : public CHudElemBase<CHudStrafeGuide>
{
public:
	virtual void Init();
	virtual void VidInit();
	virtual void Draw(float time);

	void Update(struct ref_params_s *ppmove);

private:
	double angles[6] = { 0. };

	std::complex<double> lastSimvel = 0.;
};

#endif
