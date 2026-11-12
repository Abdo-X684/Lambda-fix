// BHLX options menu (VGUI1 panel). See bhlx_menu.h.
#include "hud.h"
#include "cl_util.h"
#include "vgui_TeamFortressViewport.h"
#include "vgui_checkbutton2.h"
#include "bhlx_menu.h"

#include <string.h>

namespace {

struct BhlxOption
{
    const char* cvar;   // engine cvar name
    const char* label;  // text shown next to the checkbox
};

// v1: only settings whose code already exists in this tree.
const BhlxOption g_Options[] = {
    {"cl_autojump", "Autojump (hold jump)"},
    {"cl_autojump_priority", "Autojump priority over ducktap"},
    {"hud_speedometer", "Speedometer"},
    {"hud_speedometer_below_cross", "Speedometer below crosshair"},
    {"hud_jumpspeed", "Jump speed"},
    {"hud_jumpspeed_below_cross", "Jump speed below crosshair"},
    {"hud_strafeguide", "Strafe guide"},
};
const int g_NumOptions = sizeof(g_Options) / sizeof(g_Options[0]);

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

class CBhlxMenu : public Panel
{
public:
    CBhlxMenu(int x, int y, int wide, int tall);
    void Refresh();

    CCheckButton2* m_pChecks[g_NumOptions];
    CBhlxCheckHandler m_Handlers[g_NumOptions];
    CBhlxCloseHandler m_CloseHandler;
    bool m_bBuilt;
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
    if (!pButton || m_iIndex < 0 || m_iIndex >= g_NumOptions)
        return;
    gEngfuncs.Cvar_SetValue((char*)g_Options[m_iIndex].cvar, pButton->IsChecked() ? 1.0f : 0.0f);
}

void CBhlxCloseHandler::actionPerformed(Panel* panel)
{
    if (g_pMenu)
        g_pMenu->setVisible(false);
    SetCursorArrow(false);
}

CBhlxMenu::CBhlxMenu(int x, int y, int wide, int tall) : Panel(x, y, wide, tall), m_bBuilt(false)
{
    setPaintBackgroundEnabled(true);
    setBgColor(0, 0, 0, 200);
    setFgColor(255, 255, 255, 255);

    Label* pTitle = new Label("BHLX Options", 12, 8, wide - 24, 20);
    pTitle->setFgColor(255, 200, 0, 255);
    addChild(pTitle);

    int row = 36;
    for (int i = 0; i < g_NumOptions; i++)
    {
        CCheckButton2* pCheck = new CCheckButton2();
        pCheck->setBounds(16, row, wide - 32, 22);
        pCheck->SetText("%s", g_Options[i].label);
        pCheck->SetTextColor(255, 255, 255, 255);
        m_Handlers[i].m_iIndex = i;
        pCheck->SetHandler(&m_Handlers[i]);
        addChild(pCheck);
        m_pChecks[i] = pCheck;
        row += 28;
    }

    Button* pClose = new Button("Close", (wide - 100) / 2, row + 8, 100, 26);
    pClose->addActionSignal(&m_CloseHandler);
    addChild(pClose);

    setBounds(x, y, wide, row + 48);
    m_bBuilt = true;
}

void CBhlxMenu::Refresh()
{
    for (int i = 0; i < g_NumOptions; i++)
    {
        cvar_t* pCvar = gEngfuncs.pfnGetCvarPointer(g_Options[i].cvar);
        if (!pCvar)
        {
            // Cvar missing in this build: show it disabled, do not write to it.
            m_pChecks[i]->SetChecked(false);
            m_pChecks[i]->setEnabled(false);
            continue;
        }
        m_pChecks[i]->setEnabled(true);
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
        int wide = 360;
        g_pMenu = new CBhlxMenu((pParent->getWide() - wide) / 2, 80, wide, 300);
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
