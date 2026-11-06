// ---------------------------------------------------------------------
// Source: BugfixedHL-Rebased (tmp64/BugfixedHL-Rebased) @ 4d32095e...
// License: GPL-3.0-or-later. Ported INTO the OP4 client DLL with the
// bhl_compat compatibility layer (see docs/BHL_MERGE.md).
// Changes vs upstream are limited to includes/compat (marked COMPAT).
// ---------------------------------------------------------------------
// ---------------------------------------------------------------------
// BugfixedHL -> Opposing Force compatibility layer.
//
// BugfixedHL-Rebased is a modern rewrite of the HL client (ConVar/CvarSystem,
// CHudElem/CHudElemBase, HudPart, GetHudColor, ...). The OP4 SDK is a 2001
// GoldSrc tree with a different CHud and no ConVar class. This header supplies
// the BHL-side API on top of OP4's gEngfuncs / gHUD so that REAL BHL systems
// can be compiled inside the OP4 client DLL instead of being rewritten.
//
// See docs/BHL_MERGE.md for the exact list of compatibility shims.
// ---------------------------------------------------------------------
#ifndef BHL_COMPAT_H
#define BHL_COMPAT_H

#include "hud.h"      // OP4: CHud, gHUD, HUD_ACTIVE, MIN_ALPHA, HudPart (patched)
#include "cl_util.h"  // OP4: CVAR_CREATE, DrawConsoleString, ScaleColors, ScreenWidth/Height
#include "usercmd.h"  // OP4: usercmd_t used by ref_params_s
#include <cstdlib>
#include <cstdio>
#include <cmath>

// Version string for the merged BHL systems (BHL's appversion.h is CMake-
// generated and not part of the OP4 tree).
#define BHL_MERGE_VERSION "bhl-systems-1"

// ---- constants BHL's HUD systems expect but OP4 lacks --------------------
#ifndef FCVAR_BHL_ARCHIVE
#define FCVAR_BHL_ARCHIVE (1 << 22)  // saved into bugfixedhl.cfg by bhlcfg
#endif
#ifndef ALPHA_AMMO_FLASH
#define ALPHA_AMMO_FLASH 100
#endif
#ifndef ALPHA_AMMO_MAX
#define ALPHA_AMMO_MAX 128
#endif
#ifndef HUD_DRAW_ALWAYS
#define HUD_DRAW_ALWAYS 4
#endif
#ifndef FADE_TIME
#define FADE_TIME 100
#endif
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// ---- BHL ConVar / ConCommand / CvarSystem (from src/common/convar.h) -----
// Ported with a lazy-registration shim: BHL registers cvars in one pass at
// DLL init (CvarSystem::RegisterCvars), whereas OP4 registers them ad-hoc
// with CVAR_CREATE. GetCvar() prefers an already-registered engine cvar so
// BHL cvars never override OP4's own values.
class ConItemBase
{
public:
    ConItemBase(const char* name, const char* desc = "");
    virtual ~ConItemBase() {}
    virtual int GetType() const = 0;  // 0 = ConVar, 1 = ConCommand
    const char* GetName() const { return m_pName; }
    const char* GetDescription() const { return m_pDesc; }
    ConItemBase* Next() const { return m_pNextItem; }
    static ConItemBase* First() { return s_First; }

private:
    const char* m_pName;
    const char* m_pDesc;
    ConItemBase* m_pNextItem;
    static ConItemBase* s_First;
};

class ConVar : public ConItemBase
{
public:
    ConVar(const char* name, const char* def_val, int flags = 0, const char* desc = "");
    int GetType() const override { return 0; }
    const char* GetDefaultValue() const { return m_pDefVal; }
    int GetFlags() const { return m_iFlags; }
    cvar_t* GetCvar();
    float GetFloat();
    int GetInt();
    bool GetBool();
    const char* GetString();
    void SetValue(float val);
    void SetValue(int val);
    void SetValue(const char* val);

private:
    const char* m_pDefVal;
    int m_iFlags;
    cvar_t* m_pCvar;
};

class ConCommand : public ConItemBase
{
public:
    using CmdFunc = void (*)();
    ConCommand(const char* name, CmdFunc func, const char* desc = "");
    int GetType() const override { return 1; }
    CmdFunc GetCmdFunc() const { return m_fnCmdFunc; }
    static int ArgC();
    static const char* ArgV(int i);

private:
    CmdFunc m_fnCmdFunc;
};

#define CON_COMMAND(name, desc)                            \
    static void __CmdFunc_##name();                        \
    static ConCommand name(#name, __CmdFunc_##name, desc); \
    static void __CmdFunc_##name()

class CvarSystem
{
public:
    static void RegisterCvars();
    static ConItemBase* FindItem(const char* name);
    static ConVar* FindCvar(const char* name);
};

// ---- BHL-global cvars re-created against OP4's engine --------------------
// OP4 already registers hud_draw / default_fov itself; GetCvar() will pick up
// those instead of creating duplicates.
extern ConVar hud_dim;
extern ConVar hud_draw;
extern ConVar default_fov;

#endif  // BHL_COMPAT_H
