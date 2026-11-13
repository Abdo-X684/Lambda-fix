// BHLS Settings: BugfixedHL's "Advanced options" dialog, rebuilt in VGUI1. See bhlx_menu.h.
//
// Layout follows the original dialog: tabs, checkboxes, a Colour row with a
// Pick button, numeric text fields for crosshair size/gap/thickness/outline,
// a live crosshair preview, and OK / Cancel / Apply.
//
// Each control reads and writes an existing cvar through the engine. Nothing is
// sent to the server. Changes apply live; Cancel restores the values from when
// the dialog was opened (or from the last Apply). A control whose cvar is not
// registered in this build is shown greyed out with "(missing / غير موجود)".
//
// Every label is English / Arabic. Arabic needs a font with Arabic glyphs; the
// stock OP4 VGUI1 bitmap fonts do not have them (see the About tab note).
#include "hud.h"
#include "cl_util.h"
#include "vgui_TeamFortressViewport.h"
#include "vgui_checkbutton2.h"
#include "vgui_slider2.h"
#include "vgui_defaultinputsignal.h"
#include "VGUI_IntChangeSignal.h"
#include "VGUI_ActionSignal.h"
#include "VGUI_TextEntry.h"
#include "bhlx_menu.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace {

enum BhlxPage
{
    PAGE_GENERAL = 0,
    PAGE_HUD,
    PAGE_CHAT,
    PAGE_SCOREBOARD,
    PAGE_CROSSHAIR,
    PAGE_ABOUT,
    NUM_PAGES
};

const char* g_PageNames[NUM_PAGES] = {
    "General / عام",
    "HUD / الواجهة",
    "Chat / الدردشة",
    "Scoreboard / لوحة النتائج",
    "Crosshair / المؤشر",
    "About / حول",
};

const int WIDE = 600;
const int TALL = 400;
const int COL_X[2] = {16, 304};
const int COL_W = 280;
const int ROW_TOP = 110;
const int ROW_H = 24;
const int SLIDER_H = 44;
const int MAX_PAGE_ITEMS = 48;

struct BhlxEntry
{
    int page;
    int col;
    const char* cvar;   // engine cvar name
    const char* label;  // English / Arabic
};

const BhlxEntry g_Entries[] = {
    // General, column 1
    {PAGE_GENERAL, 0, "cl_autojump", "Autojump / القفز التلقائي"},
    {PAGE_GENERAL, 0, "cl_autojump_priority", "Autojump priority / أولوية القفز"},
    {PAGE_GENERAL, 0, "cl_killsound", "Kill sound / صوت القتل"},
    {PAGE_GENERAL, 0, "cl_enable_html_motd", "HTML MOTD / نافذة HTML"},
    {PAGE_GENERAL, 0, "results_demo_autorecord", "Auto-record demos / تسجيل الديمو تلقائياً"},
    // General, column 2 (Models)
    {PAGE_GENERAL, 1, "cl_forceenemycolors", "Enemy colours / ألوان الأعداء"},
    {PAGE_GENERAL, 1, "cl_forceteammatescolors", "Teammate colours / ألوان الزملاء"},
    {PAGE_GENERAL, 1, "cl_forceteammatesmodels", "Teammate models / نماذج الزملاء"},
    {PAGE_GENERAL, 1, "cl_hidecorpses", "Hide corpses / إخفاء الجثث"},
    {PAGE_GENERAL, 1, "cl_noshells", "No shell casings / بدون أغلفة"},
    {PAGE_GENERAL, 1, "cl_righthand", "Right-hand view / اليد اليمنى"},
    {PAGE_GENERAL, 1, "cl_bobtilt", "Angled view bob / ترنح الرؤية"},  // OP4 cvar; same effect as BHL cl_bob_angled
    {PAGE_GENERAL, 1, "r_drawviewmodel", "Draw viewmodel / إظهار السلاح"},
    // HUD, column 1
    {PAGE_HUD, 0, "hud_speedometer", "Speedometer / عداد السرعة"},
    {PAGE_HUD, 0, "hud_speedometer_below_cross", "Speedometer under cross / السرعة تحت المؤشر"},
    {PAGE_HUD, 0, "hud_jumpspeed", "Jump speed / سرعة القفز"},
    {PAGE_HUD, 0, "hud_jumpspeed_below_cross", "Jump speed under cross / سرعة القفز تحت المؤشر"},
    {PAGE_HUD, 0, "hud_strafeguide", "Strafe guide / دليل الانعطاف"},
    {PAGE_HUD, 0, "hud_timer", "Timer / المؤقت"},
    {PAGE_HUD, 0, "hud_rainbow", "Rainbow colour / ألوان قوس قزح"},
    // HUD, column 2
    {PAGE_HUD, 1, "hud_weapon", "Weapon HUD / واجهة السلاح"},
    {PAGE_HUD, 1, "hud_centerid", "Centre item ID / معرّف الهدف"},
    {PAGE_HUD, 1, "hud_dim", "Dim when idle / تعتيم عند الخمول"},
    {PAGE_HUD, 1, "hud_draw", "Draw HUD / إظهار الواجهة"},
    {PAGE_HUD, 1, "hud_menu_fkeys", "F-key menus / قوائم مفاتيح F"},
    {PAGE_HUD, 1, "hud_deathnotice_vgui", "VGUI death notices / إشعارات الموت"},
    // Chat
    {PAGE_CHAT, 0, "hud_saytext", "Show chat text / إظهار نص الدردشة"},
    {PAGE_CHAT, 0, "hud_saytext_sound", "Chat sound / صوت الدردشة"},
    {PAGE_CHAT, 0, "cl_mute_all_comms", "Mute all chat / كتم كل الدردشة"},
    // Scoreboard
    {PAGE_SCOREBOARD, 0, "hud_scoreboard_showavatars", "Avatars / الصور الرمزية"},
    {PAGE_SCOREBOARD, 0, "hud_scoreboard_showsteamid", "SteamID / معرّف SteamID"},
    {PAGE_SCOREBOARD, 0, "hud_scoreboard_showeff", "Efficiency / الكفاءة"},
    {PAGE_SCOREBOARD, 0, "hud_scoreboard_showloss", "Packet loss / فقدان الحزم"},
    // Crosshair (layout is custom; see BuildCrosshairPage)
    {PAGE_CROSSHAIR, 0, "cl_cross_enable", "Enable crosshair / تفعيل المؤشر"},
    {PAGE_CROSSHAIR, 0, "cl_cross_dot", "Show centre dot / النقطة الوسطى"},
    {PAGE_CROSSHAIR, 0, "cl_cross_t", "Remove top line (T) / إزالة الخط العلوي"},
};
const int g_NumEntries = sizeof(g_Entries) / sizeof(g_Entries[0]);

struct BhlxSlider
{
    int page;
    int col;
    const char* cvar;
    const char* label;
    int min;
    int max;
};

const BhlxSlider g_Sliders[] = {
    {PAGE_GENERAL, 0, "default_fov", "Default FOV / زاوية الرؤية الافتراضية", 75, 120},
    {PAGE_HUD, 1, "hud_scale", "HUD scale / حجم الواجهة", 50, 150},
    {PAGE_CHAT, 0, "hud_saytext_time", "Chat text time / مدة نص الدردشة", 1, 10},
};
const int g_NumSliders = sizeof(g_Sliders) / sizeof(g_Sliders[0]);

// Numeric crosshair values, shown as text fields (as in the original dialog).
struct BhlxField
{
    const char* cvar;
    const char* label;
    int min;
    int max;
};

const BhlxField g_Fields[] = {
    {"cl_cross_size", "Size / الحجم", 0, 30},
    {"cl_cross_gap", "Gap / الفجوة", 0, 30},
    {"cl_cross_thickness", "Thickness / السماكة", 1, 10},
    {"cl_cross_outline_thickness", "Outline / الحافة", 0, 5},
};
const int g_NumFields = sizeof(g_Fields) / sizeof(g_Fields[0]);

const char* const CROSS_RED = "cl_cross_red";
const char* const CROSS_GREEN = "cl_cross_green";
const char* const CROSS_BLUE = "cl_cross_blue";

// Palette for the Pick popup (r, g, b).
const int g_PaletteCount = 12;
const int g_Palette[g_PaletteCount][3] = {
    {0, 255, 255}, {255, 255, 255}, {255, 0, 0},    {0, 255, 0},     {0, 0, 255},    {255, 255, 0},
    {255, 128, 0}, {255, 0, 255},   {255, 128, 192}, {128, 0, 255},  {128, 128, 128}, {0, 0, 0},
};

// Every cvar the dialog edits. Cancel restores these.
const int SNAP_MAX = 64;
float g_SnapValue[SNAP_MAX];
bool g_SnapValid[SNAP_MAX];
int g_SnapCount = 0;

bool g_bSuppress = false;  // true while Refresh() writes control values; handlers ignore those writes

const char* SnapName(int i)
{
    if (i < g_NumEntries)
        return g_Entries[i].cvar;
    i -= g_NumEntries;
    if (i < g_NumSliders)
        return g_Sliders[i].cvar;
    i -= g_NumSliders;
    if (i < g_NumFields)
        return g_Fields[i].cvar;
    i -= g_NumFields;
    if (i == 0)
        return CROSS_RED;
    if (i == 1)
        return CROSS_GREEN;
    return CROSS_BLUE;
}

int CvarInt(const char* name, int def)
{
    cvar_t* p = gEngfuncs.pfnGetCvarPointer((char*)name);
    return p ? (int)p->value : def;
}

bool CvarExists(const char* name)
{
    return gEngfuncs.pfnGetCvarPointer((char*)name) != NULL;
}

void SetCvar(const char* name, float value)
{
    gEngfuncs.Cvar_SetValue((char*)name, value);
}

void TakeSnapshot()
{
    g_SnapCount = g_NumEntries + g_NumSliders + g_NumFields + 3;
    for (int i = 0; i < g_SnapCount && i < SNAP_MAX; i++)
    {
        cvar_t* p = gEngfuncs.pfnGetCvarPointer((char*)SnapName(i));
        g_SnapValid[i] = (p != NULL);
        g_SnapValue[i] = p ? p->value : 0.0f;
    }
}

void RestoreSnapshot()
{
    for (int i = 0; i < g_SnapCount && i < SNAP_MAX; i++)
    {
        if (g_SnapValid[i])
            SetCvar(SnapName(i), g_SnapValue[i]);
    }
}

void SetCursorArrow(bool bArrow)
{
    App* pApp = App::getInstance();
    if (!pApp || !pApp->getScheme())
        return;
    pApp->setCursorOveride(pApp->getScheme()->getCursor(bArrow ? Scheme::scu_arrow : Scheme::scu_none));
}

// "English / Arabic" label, with a suffix when the cvar is not in this build.
void MakeLabel(char* out, int outLen, const char* label, bool bExists)
{
    if (bExists)
        snprintf(out, outLen, "%s", label);
    else
        snprintf(out, outLen, "%s  (missing / غير موجود)", label);
}

class CBhlxMenu;
CBhlxMenu* g_pMenu = NULL;
Panel* g_pMenuParent = NULL;

// Shows the crosshair as configured, over a plain background.
class CCrossPreview : public Panel
{
public:
    CCrossPreview(int x, int y, int wide, int tall) : Panel(x, y, wide, tall)
    {
        setPaintBackgroundEnabled(true);
    }

    void DrawCross(int cx, int cy, int gap, int size, int thick, bool tshape, bool dot, int extra)
    {
        int g = gap - extra;
        if (g < 0)
            g = 0;
        int s = size + extra;
        int t = thick + 2 * extra;
        if (t < 1)
            t = 1;
        int half = t / 2;
        int top = cy - half;
        int bot = top + t;
        int left = cx - half;
        int right = left + t;

        drawFilledRect(cx - g - s, top, cx - g, bot);  // left arm
        drawFilledRect(cx + g, top, cx + g + s, bot);  // right arm
        if (!tshape)
            drawFilledRect(left, cy - g - s, right, cy - g);  // top arm
        drawFilledRect(left, cy + g, right, cy + g + s);  // bottom arm
        if (dot)
            drawFilledRect(left, top, right, bot);
    }

    void paintBackground() override
    {
        int w = _size[0];
        int h = _size[1];
        // Stand-in for the game scene (alpha 0 = opaque in VGUI1).
        drawSetColor(70, 100, 140, 0);
        drawFilledRect(0, 0, w, h / 2);
        drawSetColor(92, 92, 84, 0);
        drawFilledRect(0, h / 2, w, h);

        if (!CvarInt("cl_cross_enable", 1))
            return;

        int cx = w / 2;
        int cy = h / 2;
        int gap = CvarInt("cl_cross_gap", 4);
        int size = CvarInt("cl_cross_size", 6);
        int thick = CvarInt("cl_cross_thickness", 2);
        int outline = CvarInt("cl_cross_outline_thickness", 0);
        bool tshape = CvarInt("cl_cross_t", 0) != 0;
        bool dot = CvarInt("cl_cross_dot", 0) != 0;

        if (outline > 0)
        {
            drawSetColor(0, 0, 0, 0);
            DrawCross(cx, cy, gap, size, thick, tshape, dot, outline);
        }
        drawSetColor(CvarInt(CROSS_RED, 0), CvarInt(CROSS_GREEN, 255), CvarInt(CROSS_BLUE, 255), 0);
        DrawCross(cx, cy, gap, size, thick, tshape, dot, 0);
    }
};

// Colour swatch for the crosshair colour row (not clickable).
class CColorView : public Panel
{
public:
    CColorView(int x, int y, int wide, int tall) : Panel(x, y, wide, tall)
    {
        setPaintBackgroundEnabled(true);
    }

    void paintBackground() override
    {
        drawSetColor(0, 0, 0, 0);
        drawFilledRect(0, 0, _size[0], _size[1]);
        drawSetColor(CvarInt(CROSS_RED, 0), CvarInt(CROSS_GREEN, 255), CvarInt(CROSS_BLUE, 255), 0);
        drawFilledRect(2, 2, _size[0] - 2, _size[1] - 2);
    }
};

// One swatch in the Pick popup. Clicking it sets the crosshair colour.
class CSwatch : public Panel, public CDefaultInputSignal
{
public:
    int m_r, m_g, m_b;

    CSwatch(int r, int g, int b, int x, int y, int wide, int tall) : Panel(x, y, wide, tall), m_r(r), m_g(g), m_b(b)
    {
        setPaintBackgroundEnabled(true);
        addInputSignal(this);
    }

    void paintBackground() override
    {
        drawSetColor(m_r, m_g, m_b, 0);
        drawFilledRect(0, 0, _size[0], _size[1]);
    }

    void mousePressed(MouseCode code, Panel* panel) override;
};

class CColorPopup : public Panel
{
public:
    CColorPopup(int x, int y, int wide, int tall) : Panel(x, y, wide, tall)
    {
        setPaintBackgroundEnabled(true);
    }

    void paintBackground() override
    {
        drawSetColor(40, 50, 34, 0);
        drawFilledRect(0, 0, _size[0], _size[1]);
    }
};

class CBhlxMenu;

// Button actions: tabs, OK/Cancel/Apply, the X button, Pick and the popup close.
enum BhlxAction
{
    ACT_TAB = 0,
    ACT_OK,
    ACT_CANCEL,
    ACT_APPLY,
    ACT_PICK,
    ACT_PICK_CLOSE,
};

class CBhlxButtonHandler : public ActionSignal
{
public:
    int m_iAction;
    int m_iParam;
    CBhlxButtonHandler() : m_iAction(0), m_iParam(0) {}
    void actionPerformed(Panel* panel) override;
};

class CBhlxCheckHandler : public ICheckButton2Handler
{
public:
    int m_iIndex;
    CBhlxCheckHandler() : m_iIndex(0) {}
    void StateChanged(CCheckButton2* pButton) override;
};

class CBhlxSliderHandler : public IntChangeSignal
{
public:
    int m_iIndex;
    Label* m_pValue;
    CBhlxSliderHandler() : m_iIndex(0), m_pValue(NULL) {}
    void intChanged(int value, Panel* panel) override;
};

class CBhlxFieldHandler : public ActionSignal
{
public:
    int m_iIndex;
    CBhlxFieldHandler() : m_iIndex(0) {}
    void actionPerformed(Panel* panel) override;
};

const int MAX_BUTTON_HANDLERS = 16;

class CBhlxMenu : public Panel
{
public:
    CBhlxMenu(int x, int y, int wide, int tall);
    void paintBackground() override;
    void SetPage(int page);
    void Refresh();
    void CommitField(int index);
    void CommitAllFields();
    void ShowPicker(bool bShow);
    void PickColor(int r, int g, int b);
    void Hide();
    void CancelAndHide();
    void ApplyChanges();
    void OkAndHide();

    CCheckButton2* m_pChecks[g_NumEntries];
    CBhlxCheckHandler m_CheckHandlers[g_NumEntries];
    Slider2* m_pSliders[g_NumSliders];
    Label* m_pSliderLabels[g_NumSliders];
    CBhlxSliderHandler m_SliderHandlers[g_NumSliders];
    TextEntry* m_pFields[g_NumFields];
    Label* m_pFieldLabels[g_NumFields];
    CBhlxFieldHandler m_FieldHandlers[g_NumFields];
    Button* m_pTabs[NUM_PAGES];
    CBhlxButtonHandler m_ButtonHandlers[MAX_BUTTON_HANDLERS];
    CCrossPreview* m_pPreview;
    CColorView* m_pColorView;
    CColorPopup* m_pPicker;
    int m_iPage;

    // Items on each page, shown or hidden with the tab.
    Panel* m_PageItems[NUM_PAGES][MAX_PAGE_ITEMS];
    int m_PageItemCount[NUM_PAGES];

private:
    void AddPageItem(int page, Panel* p);
    void BuildGeneralAndHudPages();
    void BuildCrosshairPage();
    void BuildAboutPage();
    void BuildTabsAndButtons();
    void BuildPicker();
};

void CSwatch::mousePressed(MouseCode code, Panel* panel)
{
    if (g_pMenu)
        g_pMenu->PickColor(m_r, m_g, m_b);
}

void CBhlxButtonHandler::actionPerformed(Panel* panel)
{
    if (!g_pMenu)
        return;
    switch (m_iAction)
    {
    case ACT_TAB:
        g_pMenu->SetPage(m_iParam);
        break;
    case ACT_OK:
        g_pMenu->OkAndHide();
        break;
    case ACT_CANCEL:
        g_pMenu->CancelAndHide();
        break;
    case ACT_APPLY:
        g_pMenu->ApplyChanges();
        break;
    case ACT_PICK:
        g_pMenu->ShowPicker(true);
        break;
    case ACT_PICK_CLOSE:
        g_pMenu->ShowPicker(false);
        break;
    }
}

void CBhlxCheckHandler::StateChanged(CCheckButton2* pButton)
{
    if (g_bSuppress || !pButton || m_iIndex < 0 || m_iIndex >= g_NumEntries)
        return;
    SetCvar(g_Entries[m_iIndex].cvar, pButton->IsChecked() ? 1.0f : 0.0f);
    if (g_pMenu)
        g_pMenu->Refresh();
}

void CBhlxSliderHandler::intChanged(int value, Panel* panel)
{
    if (g_bSuppress || m_iIndex < 0 || m_iIndex >= g_NumSliders)
        return;
    SetCvar(g_Sliders[m_iIndex].cvar, (float)value);
    if (m_pValue)
    {
        char text[160];
        snprintf(text, sizeof(text), "%s: %d", g_Sliders[m_iIndex].label, value);
        m_pValue->setText("%s", text);
    }
}

void CBhlxFieldHandler::actionPerformed(Panel* panel)
{
    if (g_pMenu)
        g_pMenu->CommitField(m_iIndex);
}

CBhlxMenu::CBhlxMenu(int x, int y, int wide, int tall) : Panel(x, y, wide, tall), m_pPreview(NULL), m_pColorView(NULL), m_pPicker(NULL), m_iPage(0)
{
    setPaintBackgroundEnabled(true);
    setFgColor(255, 255, 255, 255);
    for (int p = 0; p < NUM_PAGES; p++)
        m_PageItemCount[p] = 0;

    // Title bar and close (X) button.
    Label* pTitle = new Label("BHLS Settings / إعدادات BHLS", 12, 6, wide - 60, 20);
    pTitle->setFgColor(255, 200, 0, 255);
    addChild(pTitle);

    BuildTabsAndButtons();
    BuildGeneralAndHudPages();
    BuildCrosshairPage();
    BuildAboutPage();
    BuildPicker();

    setBounds(x, y, wide, tall);
    SetPage(0);
}

void CBhlxMenu::AddPageItem(int page, Panel* p)
{
    if (m_PageItemCount[page] < MAX_PAGE_ITEMS)
        m_PageItems[page][m_PageItemCount[page]++] = p;
    addChild(p);
}

void CBhlxMenu::BuildTabsAndButtons()
{
    // Title-bar close button: same as Cancel.
    CBhlxButtonHandler* pX = &m_ButtonHandlers[MAX_BUTTON_HANDLERS - 1];
    pX->m_iAction = ACT_CANCEL;
    Button* pClose = new Button("X", WIDE - 28, 4, 22, 20);
    pClose->addActionSignal(pX);
    addChild(pClose);

    // Tabs: three per row, two rows, English on top, Arabic after the slash.
    int tabW = (WIDE - 24 - 8) / 3;
    for (int p = 0; p < NUM_PAGES; p++)
    {
        int row = p / 3;
        int col = p % 3;
        CBhlxButtonHandler* pH = &m_ButtonHandlers[p];
        pH->m_iAction = ACT_TAB;
        pH->m_iParam = p;
        m_pTabs[p] = new Button(g_PageNames[p], 12 + col * (tabW + 4), 32 + row * 26, tabW, 22);
        m_pTabs[p]->addActionSignal(pH);
        addChild(m_pTabs[p]);
    }

    // Bottom buttons: OK, Cancel, Apply (bottom right, as in the original).
    int by = TALL - 40;
    CBhlxButtonHandler* pOk = &m_ButtonHandlers[NUM_PAGES];
    pOk->m_iAction = ACT_OK;
    Button* pOkBtn = new Button("OK / موافق", WIDE - 324, by, 96, 26);
    pOkBtn->addActionSignal(pOk);
    addChild(pOkBtn);

    CBhlxButtonHandler* pCancel = &m_ButtonHandlers[NUM_PAGES + 1];
    pCancel->m_iAction = ACT_CANCEL;
    Button* pCancelBtn = new Button("Cancel / إلغاء", WIDE - 216, by, 96, 26);
    pCancelBtn->addActionSignal(pCancel);
    addChild(pCancelBtn);

    CBhlxButtonHandler* pApply = &m_ButtonHandlers[NUM_PAGES + 2];
    pApply->m_iAction = ACT_APPLY;
    Button* pApplyBtn = new Button("Apply / تطبيق", WIDE - 108, by, 96, 26);
    pApplyBtn->addActionSignal(pApply);
    addChild(pApplyBtn);
}

void CBhlxMenu::BuildGeneralAndHudPages()
{
    int cursorY[NUM_PAGES][2];
    for (int p = 0; p < NUM_PAGES; p++)
        for (int c = 0; c < 2; c++)
            cursorY[p][c] = ROW_TOP;

    // Column headers (General and Models).
    Label* pHdr0 = new Label("General / عام", COL_X[0], 88, COL_W, 18);
    pHdr0->setFgColor(255, 200, 0, 255);
    AddPageItem(PAGE_GENERAL, pHdr0);
    Label* pHdr1 = new Label("Models / النماذج", COL_X[1], 88, COL_W, 18);
    pHdr1->setFgColor(255, 200, 0, 255);
    AddPageItem(PAGE_GENERAL, pHdr1);

    // Checkboxes
    for (int i = 0; i < g_NumEntries; i++)
    {
        const BhlxEntry& e = g_Entries[i];
        if (e.page == PAGE_CROSSHAIR)
            continue;  // built in BuildCrosshairPage
        int y = cursorY[e.page][e.col];
        cursorY[e.page][e.col] += ROW_H;

        bool bExists = CvarExists(e.cvar);
        char text[200];
        MakeLabel(text, sizeof(text), e.label, bExists);

        CCheckButton2* pCheck = new CCheckButton2();
        pCheck->setBounds(COL_X[e.col], y, COL_W, 22);
        pCheck->SetText("%s", text);
        pCheck->SetTextColor(bExists ? 255 : 130, bExists ? 255 : 130, bExists ? 255 : 130, 255);
        pCheck->setEnabled(bExists);

        m_CheckHandlers[i].m_iIndex = i;
        pCheck->SetHandler(&m_CheckHandlers[i]);
        m_pChecks[i] = pCheck;
        AddPageItem(e.page, pCheck);
    }

    // Sliders: label row, then slider row.
    for (int i = 0; i < g_NumSliders; i++)
    {
        const BhlxSlider& s = g_Sliders[i];
        int y = cursorY[s.page][s.col];
        cursorY[s.page][s.col] += SLIDER_H;
        bool bExists = CvarExists(s.cvar);

        char text[200];
        MakeLabel(text, sizeof(text), s.label, bExists);
        Label* pLabel = new Label(text, COL_X[s.col], y, COL_W, 18);
        pLabel->setFgColor(bExists ? 255 : 130, bExists ? 255 : 130, bExists ? 255 : 130, 255);
        m_pSliderLabels[i] = pLabel;
        AddPageItem(s.page, pLabel);

        Slider2* pSlider = new Slider2(COL_X[s.col], y + 18, COL_W - 8, 16, false);
        pSlider->setRange(s.min, s.max);
        pSlider->setEnabled(bExists);
        m_SliderHandlers[i].m_iIndex = i;
        m_SliderHandlers[i].m_pValue = pLabel;
        pSlider->addIntChangeSignal(&m_SliderHandlers[i]);
        m_pSliders[i] = pSlider;
        AddPageItem(s.page, pSlider);
    }

    // Greyed-out note for the General/HUD/Chat/Scoreboard pages.
    Label* pNote = new Label("Grey = not ported to this build yet. / الرمادي = غير منقول بعد", 16, TALL - 66, WIDE - 32, 18);
    pNote->setFgColor(200, 200, 200, 255);
    AddPageItem(PAGE_GENERAL, pNote);
}

void CBhlxMenu::BuildCrosshairPage()
{
    // Checkboxes at the top of the left column. The generic loop skips this page.
    int row = 0;
    for (int i = 0; i < g_NumEntries; i++)
    {
        const BhlxEntry& e = g_Entries[i];
        if (e.page != PAGE_CROSSHAIR)
            continue;
        int y = ROW_TOP + row * ROW_H;
        row++;

        bool bExists = CvarExists(e.cvar);
        char text[200];
        MakeLabel(text, sizeof(text), e.label, bExists);

        CCheckButton2* pCheck = new CCheckButton2();
        pCheck->setBounds(COL_X[0], y, COL_W, 22);
        pCheck->SetText("%s", text);
        pCheck->SetTextColor(bExists ? 255 : 130, bExists ? 255 : 130, bExists ? 255 : 130, 255);
        pCheck->setEnabled(bExists);
        m_CheckHandlers[i].m_iIndex = i;
        pCheck->SetHandler(&m_CheckHandlers[i]);
        m_pChecks[i] = pCheck;
        AddPageItem(PAGE_CROSSHAIR, pCheck);
    }

    // Colour row: label, swatch, Pick button.
    int colorY = ROW_TOP + row * ROW_H + 6;
    Label* pColorLabel = new Label("Colour / اللون", COL_X[0], colorY, 120, 22);
    AddPageItem(PAGE_CROSSHAIR, pColorLabel);
    m_pColorView = new CColorView(140, colorY - 2, 40, 22);
    AddPageItem(PAGE_CROSSHAIR, m_pColorView);
    CBhlxButtonHandler* pPick = &m_ButtonHandlers[NUM_PAGES + 3];
    pPick->m_iAction = ACT_PICK;
    Button* pPickBtn = new Button("Pick / اختيار", 190, colorY - 2, 110, 24);
    pPickBtn->addActionSignal(pPick);
    AddPageItem(PAGE_CROSSHAIR, pPickBtn);

    // Numeric text fields.
    int fieldY = colorY + 34;
    for (int i = 0; i < g_NumFields; i++)
    {
        const BhlxField& f = g_Fields[i];
        bool bExists = CvarExists(f.cvar);
        char text[200];
        MakeLabel(text, sizeof(text), f.label, bExists);
        Label* pLabel = new Label(text, COL_X[0], fieldY, 150, 20);
        pLabel->setFgColor(bExists ? 255 : 130, bExists ? 255 : 130, bExists ? 255 : 130, 255);
        m_pFieldLabels[i] = pLabel;
        AddPageItem(PAGE_CROSSHAIR, pLabel);

        TextEntry* pField = new TextEntry("", 170, fieldY - 2, 80, 22);
        pField->setEnabled(bExists);
        m_FieldHandlers[i].m_iIndex = i;
        pField->addActionSignal(&m_FieldHandlers[i]);
        m_pFields[i] = pField;
        AddPageItem(PAGE_CROSSHAIR, pField);
        fieldY += 28;
    }

    // Live preview on the right.
    m_pPreview = new CCrossPreview(330, ROW_TOP, 254, 200);
    AddPageItem(PAGE_CROSSHAIR, m_pPreview);
}

void CBhlxMenu::BuildAboutPage()
{
    const char* lines[] = {
        "BHLS Settings for OP4 / إعدادات BHLS لمحرك OP4",
        "Moved from BugfixedHL's Advanced options (VGUI2) to VGUI1.",
        "منقولة من خيارات BugfixedHL المتقدمة (VGUI2) إلى VGUI1.",
        "Apply saves now. Cancel reverts to the last saved values.",
        "تطبيق يحفظ الآن. إلغاء يعيد آخر قيم محفوظة.",
        "Grey items are not ported to this build yet.",
        "العناصر الرمادية غير منقولة في هذا البناء بعد.",
        "Arabic text needs an Arabic-capable font. OP4's stock VGUI1 fonts lack it.",
        "النص العربي يحتاج خطاً يدعم العربية. خطوط OP4 الأصلية لا تدعمه.",
    };
    int y = ROW_TOP;
    for (unsigned int i = 0; i < sizeof(lines) / sizeof(lines[0]); i++)
    {
        Label* pLine = new Label(lines[i], 16, y, WIDE - 32, 20);
        pLine->setFgColor(255, 255, 255, 255);
        AddPageItem(PAGE_ABOUT, pLine);
        y += 26;
    }
}

void CBhlxMenu::BuildPicker()
{
    int pw = 260;
    int ph = 150;
    m_pPicker = new CColorPopup((WIDE - pw) / 2, ROW_TOP, pw, ph);
    m_pPicker->setVisible(false);

    Label* pTitle = new Label("Pick colour / اختر اللون", 10, 8, pw - 20, 20);
    pTitle->setFgColor(255, 200, 0, 255);
    m_pPicker->addChild(pTitle);

    for (int i = 0; i < g_PaletteCount; i++)
    {
        int c = i % 6;
        int r = i / 6;
        CSwatch* pSwatch = new CSwatch(g_Palette[i][0], g_Palette[i][1], g_Palette[i][2], 10 + c * 40, 34 + r * 40, 30, 30);
        m_pPicker->addChild(pSwatch);
    }

    CBhlxButtonHandler* pClose = &m_ButtonHandlers[NUM_PAGES + 4];
    pClose->m_iAction = ACT_PICK_CLOSE;
    Button* pCloseBtn = new Button("Close / إغلاق", (pw - 100) / 2, ph - 34, 100, 24);
    pCloseBtn->addActionSignal(pClose);
    m_pPicker->addChild(pCloseBtn);

    addChild(m_pPicker);
}

void CBhlxMenu::paintBackground()
{
    // Opaque dark olive (alpha 0 = solid in VGUI1). With a transparent panel the
    // white text sits on the bright game scene and cannot be read.
    drawSetColor(76, 90, 64, 0);
    drawFilledRect(0, 0, _size[0], _size[1]);
    // Title bar.
    drawSetColor(52, 62, 44, 0);
    drawFilledRect(0, 0, _size[0], 28);
}

void CBhlxMenu::SetPage(int page)
{
    if (page < 0 || page >= NUM_PAGES)
        return;
    m_iPage = page;
    for (int p = 0; p < NUM_PAGES; p++)
    {
        for (int i = 0; i < m_PageItemCount[p]; i++)
            m_PageItems[p][i]->setVisible(p == page);
        if (m_pTabs[p])
            m_pTabs[p]->setFgColor(255, p == page ? 200 : 255, p == page ? 0 : 255, 255);
    }
    ShowPicker(false);
}

void CBhlxMenu::Refresh()
{
    g_bSuppress = true;

    for (int i = 0; i < g_NumEntries; i++)
    {
        cvar_t* pCvar = gEngfuncs.pfnGetCvarPointer((char*)g_Entries[i].cvar);
        if (!m_pChecks[i])
            continue;
        m_pChecks[i]->SetChecked(pCvar ? pCvar->value != 0.0f : false);
    }

    for (int i = 0; i < g_NumSliders; i++)
    {
        bool bExists = CvarExists(g_Sliders[i].cvar);
        int value = CvarInt(g_Sliders[i].cvar, g_Sliders[i].min);
        if (value < g_Sliders[i].min)
            value = g_Sliders[i].min;
        if (value > g_Sliders[i].max)
            value = g_Sliders[i].max;
        m_pSliders[i]->setValue(value);
        char text[200];
        char base[200];
        MakeLabel(base, sizeof(base), g_Sliders[i].label, bExists);
        snprintf(text, sizeof(text), "%s: %d", base, value);
        m_pSliderLabels[i]->setText("%s", text);
    }

    for (int i = 0; i < g_NumFields; i++)
    {
        char buf[32];
        int value = CvarInt(g_Fields[i].cvar, g_Fields[i].min);
        if (value < g_Fields[i].min)
            value = g_Fields[i].min;
        if (value > g_Fields[i].max)
            value = g_Fields[i].max;
        snprintf(buf, sizeof(buf), "%d", value);
        m_pFields[i]->setText(buf, (int)strlen(buf));
    }

    g_bSuppress = false;
    if (m_pColorView)
        m_pColorView->repaint();
    if (m_pPreview)
        m_pPreview->repaint();
}

void CBhlxMenu::CommitField(int index)
{
    if (index < 0 || index >= g_NumFields)
        return;
    char buf[32];
    m_pFields[index]->getText(0, buf, sizeof(buf));
    int value = atoi(buf);
    if (value < g_Fields[index].min)
        value = g_Fields[index].min;
    if (value > g_Fields[index].max)
        value = g_Fields[index].max;
    SetCvar(g_Fields[index].cvar, (float)value);
    Refresh();
}

void CBhlxMenu::CommitAllFields()
{
    for (int i = 0; i < g_NumFields; i++)
        CommitField(i);
}

void CBhlxMenu::ShowPicker(bool bShow)
{
    if (m_pPicker)
        m_pPicker->setVisible(bShow);
}

void CBhlxMenu::PickColor(int r, int g, int b)
{
    SetCvar(CROSS_RED, (float)r);
    SetCvar(CROSS_GREEN, (float)g);
    SetCvar(CROSS_BLUE, (float)b);
    ShowPicker(false);
    Refresh();
}

void CBhlxMenu::ApplyChanges()
{
    CommitAllFields();
    TakeSnapshot();
    Refresh();
}

void CBhlxMenu::OkAndHide()
{
    ApplyChanges();
    Hide();
}

void CBhlxMenu::CancelAndHide()
{
    RestoreSnapshot();
    Refresh();
    Hide();
}

void CBhlxMenu::Hide()
{
    ShowPicker(false);
    setVisible(false);
    SetCursorArrow(false);
}

void BHLX_ToggleMenu()
{
    // Prefer the TF viewport. If it is not created yet, use the engine VGUI root
    // so the menu still opens (VGUI1 root exists before the viewport does).
    Panel* pParent = gViewPort ? (Panel*)gViewPort : (Panel*)gEngfuncs.VGui_GetPanel();
    if (!pParent)
    {
        gEngfuncs.pfnConsolePrint("[BHLX] VGUI is not ready yet. Load a map, then type bhls_settings again.\n");
        return;
    }
    if (!g_pMenu || g_pMenuParent != pParent)
    {
        g_pMenu = new CBhlxMenu((pParent->getWide() - WIDE) / 2, 40, WIDE, TALL);
        pParent->addChild(g_pMenu);
        g_pMenuParent = pParent;
    }
    if (g_pMenu->isVisible())
    {
        // Closing with the command keeps the current values (like Apply).
        g_pMenu->ApplyChanges();
        g_pMenu->Hide();
        return;
    }
    g_pMenu->Refresh();
    TakeSnapshot();
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
    gEngfuncs.pfnAddCommand("bhls_settings", BHLX_MenuCommand);
    // BugfixedHL opens its old Advanced Options dialog with this command; route it to the translated menu.
    gEngfuncs.pfnAddCommand("gameui_cl_open_adv_options", BHLX_MenuCommand);
    gEngfuncs.pfnConsolePrint("[BHLS] settings menu loaded. Type bhls_settings (or bhlx_menu) to open it.\n");
}
