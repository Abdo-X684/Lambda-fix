// ---------------------------------------------------------------------
// Source: BugfixedHL-Rebased (tmp64/BugfixedHL-Rebased) @ 4d32095e...
// License: GPL-3.0-or-later. Ported INTO the OP4 client DLL with the
// bhl_compat compatibility layer (see docs/BHL_MERGE.md).
// Changes vs upstream are limited to includes/compat (marked COMPAT).
// ---------------------------------------------------------------------
#include "bhl_compat.h"  // COMPAT: BHL ConVar / constants on OP4
#include "base.h"

//----------------------------------------------------------
// CHudElem
//----------------------------------------------------------
CHudElem::~CHudElem() { }
void CHudElem::Init() { }
void CHudElem::VidInit() { }
void CHudElem::Draw(float flTime) { }
void CHudElem::Think() { }
void CHudElem::Reset() { }
void CHudElem::InitHudData() { }
