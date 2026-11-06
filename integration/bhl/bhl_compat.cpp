// ---------------------------------------------------------------------
// BugfixedHL -> Opposing Force compatibility layer (implementation).
// Derived from BugfixedHL src/common/convar.cpp and src/game/client/hud.cpp
// (CvarSystem::RegisterCvars / RegisterHudElem), adapted to OP4's engine.
// GPL-3.0-or-later. See docs/BHL_MERGE.md.
// ---------------------------------------------------------------------
#include "bhl_compat.h"
#include <cstring>

#include "base.h"
#include "speedometer.h"
#include "jumpspeed.h"
#include "strafeguide.h"
#include "bhlcfg.h"
#include "ref_params.h"   // OP4: common/ref_params.h (simvel, movevars, cmd)

// ---------------------------------------------------------------------
// ConItemBase / ConVar / ConCommand / CvarSystem
// ---------------------------------------------------------------------
ConItemBase* ConItemBase::s_First = nullptr;

ConItemBase::ConItemBase(const char* name, const char* desc)
    : m_pName(name), m_pDesc(desc), m_pNextItem(s_First)
{
    s_First = this;
}

ConVar::ConVar(const char* name, const char* def_val, int flags, const char* desc)
    : ConItemBase(name, desc), m_pDefVal(def_val), m_iFlags(flags), m_pCvar(nullptr)
{
}

cvar_t* ConVar::GetCvar()
{
    if (m_pCvar)
        return m_pCvar;
    // COMPAT: prefer an existing engine cvar (OP4 registers hud_draw,
    // default_fov, ... itself) before creating a new one.
    if (gEngfuncs.pfnGetCvarPointer)
        m_pCvar = gEngfuncs.pfnGetCvarPointer(GetName());
    if (!m_pCvar && gEngfuncs.pfnRegisterVariable)
        m_pCvar = gEngfuncs.pfnRegisterVariable(GetName(), m_pDefVal, m_iFlags);
    return m_pCvar;
}

float ConVar::GetFloat()
{
    cvar_t* c = GetCvar();
    return c ? c->value : static_cast<float>(std::atof(m_pDefVal));
}

int ConVar::GetInt() { return static_cast<int>(GetFloat()); }
bool ConVar::GetBool() { return GetInt() != 0; }
const char* ConVar::GetString()
{
    cvar_t* c = GetCvar();
    return c && c->string ? c->string : m_pDefVal;
}

void ConVar::SetValue(float val)
{
    if (gEngfuncs.Cvar_SetValue)
        gEngfuncs.Cvar_SetValue(GetName(), val);
}
void ConVar::SetValue(int val) { SetValue(static_cast<float>(val)); }
void ConVar::SetValue(const char* val)
{
    if (gEngfuncs.Cvar_Set)
        gEngfuncs.Cvar_Set(GetName(), const_cast<char*>(val));
}

ConCommand::ConCommand(const char* name, CmdFunc func, const char* desc)
    : ConItemBase(name, desc), m_fnCmdFunc(func)
{
}
int ConCommand::ArgC()
{
    return gEngfuncs.Cmd_Argc ? gEngfuncs.Cmd_Argc() : 0;
}
const char* ConCommand::ArgV(int i)
{
    return gEngfuncs.Cmd_Argv ? gEngfuncs.Cmd_Argv(i) : "";
}

void CvarSystem::RegisterCvars()
{
    for (ConItemBase* item = ConItemBase::First(); item; item = item->Next())
    {
        if (item->GetType() == 0)
        {
            static_cast<ConVar*>(item)->GetCvar();
        }
        else if (item->GetType() == 1)
        {
            ConCommand* cmd = static_cast<ConCommand*>(item);
            if (gEngfuncs.pfnAddCommand)
                gEngfuncs.pfnAddCommand(cmd->GetName(), cmd->GetCmdFunc());
        }
    }
}

ConItemBase* CvarSystem::FindItem(const char* name)
{
    for (ConItemBase* item = ConItemBase::First(); item; item = item->Next())
        if (item->GetName() && std::strcmp(item->GetName(), name) == 0)
            return item;
    return nullptr;
}

ConVar* CvarSystem::FindCvar(const char* name)
{
    ConItemBase* item = FindItem(name);
    return (item && item->GetType() == 0) ? static_cast<ConVar*>(item) : nullptr;
}

// ---------------------------------------------------------------------
// BHL-global cvars used by the ported HUD systems
// ---------------------------------------------------------------------
ConVar hud_dim("hud_dim", "1", FCVAR_BHL_ARCHIVE, "Dim the BHL HUD when idle");
ConVar hud_draw("hud_draw", "1", FCVAR_BHL_ARCHIVE, "OP4 hud_draw, exposed to BHL HUD elements");
ConVar default_fov("default_fov", "90", FCVAR_BHL_ARCHIVE, "OP4 default_fov, exposed to BHL strafeguide");

// ---------------------------------------------------------------------
// BHL's own ConCommand / version cvar, registered by CvarSystem.
// This is BHL's actual cvar system doing real work inside OP4.
// ---------------------------------------------------------------------
ConVar bhl_version("bhl_version", "bhl-systems-1", FCVAR_BHL_ARCHIVE,
                   "BugfixedHL systems merged into Opposing Force");

CON_COMMAND(bhl_status, "List the BugfixedHL systems merged into OP4")
{
    ConsolePrint("\n[BHL] ---- merged BugfixedHL systems -------------------\n");
    ConsolePrint("[BHL]  ConVar/CvarSystem, CHudElem HUD base\n");
    ConsolePrint("[BHL]  CHudSpeedometer  (hud_speedometer)\n");
    ConsolePrint("[BHL]  CHudJumpspeed    (hud_jumpspeed)\n");
    ConsolePrint("[BHL]  CHudStrafeGuide  (hud_strafeguide)\n");
    ConsolePrint("[BHL]  bhlcfg / bugfixedhl.cfg\n");
    ConsolePrint("[BHL]  server sv_bhl_* cvars\n");
    ConsolePrint("[BHL]  speedrun sr_* layer = optional add-on, NOT the merge\n");
    ConsolePrint("[BHL] ---------------------------------------------------\n\n");
}

// ---------------------------------------------------------------------
// CHud compatibility methods (declared into OP4 hud.h by merge/bhl.py)
// ---------------------------------------------------------------------
void CHud::GetHudColor(HudPart hudPart, int value, int& r, int& g, int& b)
{
    (void)hudPart;
    (void)value;
    // OP4 broadcasts the HUD colour into giR/giG/giB; BHL's HudPart::Common
    // is the amber HL default until that message arrives.
    extern int giR, giG, giB;
    if (giR || giG || giB)
    {
        r = giR;
        g = giG;
        b = giB;
    }
    else
    {
        r = 255;
        g = 160;
        b = 0;
    }
}

float CHud::GetHudTransparency()
{
    return 1.0f;
}

int CHud::DrawHudNumberCentered(int x, int y, int number, int r, int g, int b)
{
    char buf[24];
    std::snprintf(buf, sizeof(buf), "%d", number);
    int width = 0, height = 0;
    if (gEngfuncs.pfnDrawConsoleStringLen)
        gEngfuncs.pfnDrawConsoleStringLen(buf, &width, &height);
    else
        width = static_cast<int>(std::strlen(buf)) * m_iFontHeight;
    return DrawHudNumber(x - width / 2, y, DHN_DRAWZERO, number, r, g, b);
}

// ---------------------------------------------------------------------
// BHL system lifecycle. CHudElemBase::Get() is populated by new T() exactly
// as BHL's CHud::RegisterHudElem<T>() does.
// ---------------------------------------------------------------------
namespace {
CHudElem* g_BhlElements[3] = {};
bool g_BhlReady = false;
}

void BHL_Init()
{
    if (g_BhlReady)
        return;
    g_BhlReady = true;

    CvarSystem::RegisterCvars();
    g_BhlElements[0] = new CHudSpeedometer();
    g_BhlElements[1] = new CHudJumpspeed();
    g_BhlElements[2] = new CHudStrafeGuide();
    for (CHudElem* elem : g_BhlElements)
        elem->Init();

    bhlcfg::Init();

    ConsolePrint("\n[BHL] ================================================\n");
    ConsolePrint("[BHL]  BugfixedHL systems merged into Opposing Force\n");
    ConsolePrint("[BHL]  ConVar/CvarSystem, CHudElem, speedometer,\n");
    ConsolePrint("[BHL]  jumpspeed, strafeguide, bugfixedhl.cfg\n");
    ConsolePrint("[BHL]  hud_speedometer 1 | hud_jumpspeed 1 | hud_strafeguide 1\n");
    ConsolePrint("[BHL] ================================================\n\n");
}

void BHL_VidInit()
{
    if (!g_BhlReady)
        return;
    for (CHudElem* elem : g_BhlElements)
        elem->VidInit();
}

void BHL_Draw(float flTime)
{
    if (!g_BhlReady)
        return;
    for (CHudElem* elem : g_BhlElements)
        elem->Draw(flTime);
}

void BHL_Think()
{
    if (!g_BhlReady)
        return;
    for (CHudElem* elem : g_BhlElements)
        elem->Think();
}

void BHL_OnRefdef(struct ref_params_s* pparams)
{
    if (!g_BhlReady || !pparams)
        return;
    // Same three calls as BugfixedHL src/game/client/view.cpp:1686-1688.
    CHudSpeedometer::Get()->UpdateSpeed(pparams->simvel);
    CHudJumpspeed::Get()->UpdateSpeed(pparams->simvel);
    CHudStrafeGuide::Get()->Update(pparams);
}

void BHL_Shutdown()
{
    if (!g_BhlReady)
        return;
    bhlcfg::Shutdown();
}
