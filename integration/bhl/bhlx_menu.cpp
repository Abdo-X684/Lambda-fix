// BHLX options menu (VGUI1 panel). See bhlx_menu.h.
//
// Pages are translated from BugfixedHL's options pages (General, HUD, Chat,
// Crosshair, Scoreboard, Models). Only boolean cvars are offered as checkboxes.
// A control whose cvar is not registered in this build is shown disabled with
// the note "(not in this build)"; its feature code is not ported yet.
#include "hud.h"
#include "cl_util.h"
#include "vgui_TeamFortressViewport.h"
#include "vgui_checkbutton2.h"
#include "bhlx_menu.h"

#include <stdio.h>
#include <string.h>

namespace {

enum BhlxPage
{
    PAGE_GENERAL = 0,
    PAGE_HUD,
    PAGE_CHAT,
    PAGE_CROSSHAIR,
    PAGE_SCOREBOARD,
    PAGE_MODELS,
    NUM_PAGES
};

const char* g_PageNames[NUM_PAGES] = {"General", "HUD", "Chat", "Crosshair", "Scoreboard", "Models"};

struct BhlxEntry
{
    int page;
    const char* cvar;   // engine cvar name
    const char* label;  // text shown next to the checkbox
};

const BhlxEntry g_Entries[] = {
    // General
    {PAGE_GENERAL, "cl_autojump", "Autojump (hold jump)"},
    {PAGE_GENERAL, "cl_autojump_priority", "Autojump priority over ducktap"},
    {PAGE_GENERAL, "cl_killsound", "Kill sound"},
    {PAGE_GENERAL, "cl_mute_all_comms", "Mute all chat"},
    {PAGE_GENERAL, "cl_enable_html_motd", "HTML MOTD"},
    {PAGE_GENERAL, "results_demo_autorecord", "Auto-record demos"},
    // HUD
    {PAGE_HUD, "hud_speedometer", "Speedometer"},
    {PAGE_HUD, "hud_speedometer_below_cross", "Speedometer below crosshair"},
    {PAGE_HUD, "hud_jumpspeed", "Jump speed"},
    {PAGE_HUD, "hud_jumpspeed_below_cross", "Jump speed below crosshair"},
    {PAGE_HUD, "hud_strafeguide", "Strafe guide"},
    {PAGE_HUD, "hud_timer", "Timer"},
    {PAGE_HUD, "hud_rainbow", "Rainbow HUD colour"},
    {PAGE_HUD, "hud_weapon", "Weapon HUD"},
    {PAGE_HUD, "hud_centerid", "Center item ID"},
    {PAGE_HUD, "hud_dim", "Dim HUD when idle"},
    {PAGE_HUD, "hud_draw", "Draw HUD"},
    {PAGE_HUD, "hud_menu_fkeys", "F-key menus"},
    {PAGE_HUD, "hud_deathnotice_vgui", "VGUI death notices"},
    // Chat
    {PAGE_CHAT, "hud_saytext_sound", "Chat sound"},
    // Crosshair
    {PAGE_CROSSHAIR, "cl_cross_enable", "Crosshair enabled"},
    {PAGE_CROSSHAIR, "cl_cross_dot", "Crosshair centre dot"},
    // Scoreboard
    {PAGE_SCOREBOARD, "hud_scoreboard_showavatars", "Show avatars"},
    {PAGE_SCOREBOARD, "hud_scoreboard_showsteamid", "Show SteamID"},
    {PAGE_SCOREBOARD, "hud_scoreboard_showeff", "Show efficiency"},
    {PAGE_SCOREBOARD, "hud_scoreboard_showloss", "Show packet loss"},
    // Models
    {PAGE_MODELS, "cl_forceenemycolors", "Force enemy colours"},
    {PAGE_MODELS, "cl_forceteammatescolors", "Force teammate colours"},
    {PAGE_MODELS, "cl_forceteammatesmodels", "Force teammate models"},
    {PAGE_MODELS, "cl_hidecorpses", "Hide corpses"},
    {PAGE_MODELS, "cl_noshells", "No shell casings"},
    {PAGE_MODELS, "cl_righthand", "Right-hand viewmodel"},
    {PAGE_MODELS, "cl_bob_angled", "Angled view bob"},
    {PAGE_MODELS, "r_drawviewmodel", "Draw viewmodel"},
};
const int g_NumEntries = sizeof(g_Entries) / sizeof(g_Entries[0]);
const int MAX_ROWS = 20;

class CBhlxMenu;

class CBhlxCheckHandler : public ICheckButton2Handler
{
public:
    int m_iIndex;
    CBhlxCheckHandler() : m_iIndex(0) {}
    void StateChanged(CCheckButton2* pButton) override;
};

class CBhlxCloseHandler : public ActionSignal
{
public:
    void actionPerformed(Panel* panel) override;
};

class CBhlxTabHandler : public ActionSignal
{
public:
    int m_iPage;
    CBhlxTabHandler() : m_iPage(0) {}
    void actionPerformed(Panel* panel) override;
};

class CBhlxMenu : public Panel
{
public:
    CBhlxMenu(int x, int y, int wide, int tall);
    void SetPage(int page);
    void Refresh();

    CCheckButton2* m_pChecks[g_NumEntries];
    CBhlxCheckHandler m_Handlers[g_NumEntries];
    Button* m_pTabs[NUM_PAGES];
    CBhlxTabHandler m_TabHandlers[NUM_PAGES];
    CBhlxCloseHandler m_CloseHandler;
    Label* m_pNote;
    int m_iPage;
};

CBhlxMenu* g_pMenu = NULL;
Panel* g_pMenuParent = NULL;

void SetCursorArrow(bool bArrow)
{
    App* pApp = App::getInstance();
    if (!pApp || !pApp->getScheme())
        return;
    pApp->setCursorOveride(pApp->getScheme()->getCursor(bArrow ? Scheme::scu_arrow : Scheme::scu_none));
}

void CBhlxCheckHandler::StateChanged(CCheckButton2* pButton)
{
    if (!pButton || m_iIndex < 0 || m_iIndex >= g_NumEntries)
        return;
    gEngfuncs.Cvar_SetValue((char*)g_Entries[m_iIndex].cvar, pButton->IsChecked() ? 1.0f : 0.0f);
}

void CBhlxCloseHandler::actionPerformed(Panel* panel)
{
    if (g_pMenu)
        g_pMenu->setVisible(false);
    SetCursorArrow(false);
}

void CBhlxTabHandler::actionPerformed(Panel* panel)
{
    if (g_pMenu)
        g_pMenu->SetPage(m_iPage);
}

CBhlxMenu::CBhlxMenu(int x, int y, int wide, int tall) : Panel(x, y, wide, tall), m_pNote(NULL), m_iPage(0)
{
    setPaintBackgroundEnabled(true);
    setBgColor(0, 0, 0, 200);
    setFgColor(255, 255, 255, 255);

    Label* pTitle = new Label("BHLX Options", 12, 8, wide - 24, 20);
    pTitle->setFgColor(255, 200, 0, 255);
    addChild(pTitle);

    // Page tabs
    int tabW = (wide - 24) / NUM_PAGES;
    for (int p = 0; p < NUM_PAGES; p++)
    {
        m_TabHandlers[p].m_iPage = p;
        m_pTabs[p] = new Button(g_PageNames[p], 12 + p * tabW, 34, tabW - 2, 22);
        m_pTabs[p]->addActionSignal(&m_TabHandlers[p]);
        addChild(m_pTabs[p]);
    }

    // Checkboxes, one row list per page
    int rowOnPage[NUM_PAGES] = {0};
    int maxRows = 0;
    for (int i = 0; i < g_NumEntries; i++)
    {
        const BhlxEntry& e = g_Entries[i];
        CCheckButton2* pCheck = new CCheckButton2();
        int row = rowOnPage[e.page]++;
        pCheck->setBounds(16, 66 + row * 24, wide - 32, 22);

        bool bExists = gEngfuncs.pfnGetCvarPointer(e.cvar) != NULL;
        char text[160];
        if (bExists)
            snprintf(text, sizeof(text), "%s", e.label);
        else
            snprintf(text, sizeof(text), "%s  (not in this build)", e.label);
        pCheck->SetText("%s", text);
        pCheck->SetTextColor(bExists ? 255 : 130, bExists ? 255 : 130, bExists ? 255 : 130, 255);
        pCheck->setEnabled(bExists);

        m_Handlers[i].m_iIndex = i;
        pCheck->SetHandler(&m_Handlers[i]);
        addChild(pCheck);
        m_pChecks[i] = pCheck;
        if (rowOnPage[e.page] > maxRows)
            maxRows = rowOnPage[e.page];
    }
    if (maxRows > MAX_ROWS)
        maxRows = MAX_ROWS;

    int bottom = 66 + maxRows * 24;
    m_pNote = new Label("Grey items need features not ported to this build yet.", 16, bottom, wide - 32, 18);
    m_pNote->setFgColor(200, 200, 200, 255);
    addChild(m_pNote);

    Button* pClose = new Button("Close", (wide - 100) / 2, bottom + 26, 100, 26);
    pClose->addActionSignal(&m_CloseHandler);
    addChild(pClose);

    setBounds(x, y, wide, bottom + 66);
    SetPage(0);
}

void CBhlxMenu::SetPage(int page)
{
    if (page < 0 || page >= NUM_PAGES)
        return;
    m_iPage = page;
    for (int i = 0; i < g_NumEntries; i++)
        m_pChecks[i]->setVisible(g_Entries[i].page == page);
}

void CBhlxMenu::Refresh()
{
    for (int i = 0; i < g_NumEntries; i++)
    {
        cvar_t* pCvar = gEngfuncs.pfnGetCvarPointer(g_Entries[i].cvar);
        if (!pCvar)
        {
            m_pChecks[i]->SetChecked(false);
            continue;
        }
        m_pChecks[i]->SetChecked(pCvar->value != 0.0f);
    }
}

void BHLX_ToggleMenu()
{
    // Prefer the TF viewport. If it is not created yet, use the engine VGUI root
    // so the menu still opens (VGUI1 root exists before the viewport does).
    Panel* pParent = gViewPort ? (Panel*)gViewPort : (Panel*)gEngfuncs.VGui_GetPanel();
    if (!pParent)
    {
        gEngfuncs.pfnConsolePrint("[BHLX] VGUI is not ready yet. Load a map, then type bhlx_menu again.\n");
        return;
    }
    if (!g_pMenu || g_pMenuParent != pParent)
    {
        int wide = 440;
        g_pMenu = new CBhlxMenu((pParent->getWide() - wide) / 2, 60, wide, 400);
        pParent->addChild(g_pMenu);
        g_pMenuParent = pParent;
    }
    if (g_pMenu->isVisible())
    {
        g_pMenu->setVisible(false);
        SetCursorArrow(false);
        return;
    }
    g_pMenu->Refresh();
    g_pMenu->setVisible(true);
    g_pMenu->requestFocus();
    SetCursorArrow(true);
}

void BHLX_MenuCommand()
{
    BHLX_ToggleMenu();
}

} // namespace

void BHLX_Init()
{
    gEngfuncs.pfnAddCommand("bhlx_menu", BHLX_MenuCommand);
    gEngfuncs.pfnConsolePrint("[BHLX] options menu loaded. Type bhlx_menu to open it.\n");
}
