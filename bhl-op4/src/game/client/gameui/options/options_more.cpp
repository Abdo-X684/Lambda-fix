#include <vgui_controls/Label.h>
#include <KeyValues.h>
#include "client_vgui.h"
#include "client_steam_context.h"
#include "cvar_text_entry.h"
#include "cvar_check_button.h"
#include "options_more.h"

CMoreSubOptions::CMoreSubOptions(vgui2::Panel *parent)
    : BaseClass(parent, "MoreSubOptions")
{
	SetSize(100, 100); // Silence "parent not sized yet" warning

	m_pMOTD = new CCvarCheckButton(this, "MOTD", "#BHL_AdvOptions_General_HTML", "cl_enable_html_motd");
	m_pMOTDLabel = new vgui2::Label(this, "MOTDLabel", "#BHL_AdvOptions_General_HTML2");

	m_pLogChat = new CCvarCheckButton(this, "LogChat", "#BHL_AdvOptions_General_LogChat", "results_log_chat");
	m_pLogOther = new CCvarCheckButton(this, "LogOther", "#BHL_AdvOptions_General_LogOther", "results_log_other");
	m_pAutoDemo = new CCvarCheckButton(this, "AutoDemo", "#BHL_AdvOptions_General_AutoDemo", "results_demo_autorecord");
	m_pAutoDemoLabel = new vgui2::Label(this, "AutoDemoLabel", "#BHL_AdvOptions_General_AutoDemo2");
	m_pKeepFor = new CCvarTextEntry(this, "KeepFor", "results_demo_keepdays", CCvarTextEntry::CvarType::Int);
	m_pKeepForLabel = new vgui2::Label(this, "KeepForLabel", "#BHL_AdvOptions_General_KeepFor");
	m_pDaysLabel = new vgui2::Label(this, "DaysLabel", "#BHL_AdvOptions_General_Days");

	LoadControlSettings(VGUI2_ROOT_DIR "resource/options/MoreSubOptions.res");

	// Disable HTML MOTD if SteamAPI not available
	if (!SteamAPI_IsAvailable())
	{
		m_pMOTD->SetEnabled(false);
		m_pMOTD->SetSelected(false);
	}
}

void CMoreSubOptions::OnResetData()
{
	if (m_pMOTD->IsEnabled())
		m_pMOTD->ResetData();

	m_pLogChat->ResetData();
	m_pLogOther->ResetData();
	m_pAutoDemo->ResetData();
	m_pKeepFor->ResetData();
}

void CMoreSubOptions::OnApplyChanges()
{
	if (m_pMOTD->IsEnabled())
		m_pMOTD->ApplyChanges();

	m_pLogChat->ApplyChanges();
	m_pLogOther->ApplyChanges();
	m_pAutoDemo->ApplyChanges();
	m_pKeepFor->ApplyChanges();
}
