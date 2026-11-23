#include "options_multiplayer_root.h"
#include "options_chat.h"
#include "options_scoreboard.h"
#include "options_models.h"
#include "options_more.h"

CMultiplayerSubOptionsRoot::CMultiplayerSubOptionsRoot(vgui2::Panel *parent)
    : BaseClass(parent, "MultiplayerSubOptionsRoot")
{
	SetSize(100, 100); // Silence "parent not sized yet" warning

	AddPage((m_pChat = new CChatSubOptions(this)), "#BHL_AdvOptions_Chat");
	AddPage((m_pScoreboard = new CScoreboardSubOptions(this)), "#BHL_AdvOptions_Scores");
	AddPage((m_pModels = new CModelSubOptions(this)), "#BHL_AdvOptions_Models");
	AddPage((m_pMore = new CMoreSubOptions(this)), "#BHL_AdvOptions_More");
}

void CMultiplayerSubOptionsRoot::OnResetData()
{
	m_pChat->OnResetData();
	m_pScoreboard->OnResetData();
	m_pModels->OnResetData();
	m_pMore->OnResetData();
}

void CMultiplayerSubOptionsRoot::OnApplyChanges()
{
	m_pChat->OnApplyChanges();
	m_pScoreboard->OnApplyChanges();
	m_pModels->OnApplyChanges();
	m_pMore->OnApplyChanges();
}
