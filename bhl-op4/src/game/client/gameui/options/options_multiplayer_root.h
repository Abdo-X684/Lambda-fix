#ifndef OPTIONS_MULTIPLAYER_ROOT_H
#define OPTIONS_MULTIPLAYER_ROOT_H
#include <vgui_controls/PropertySheet.h>

class CChatSubOptions;
class CScoreboardSubOptions;
class CModelSubOptions;

// Multiplayer-only options (Chat, Scoreboard, Models) grouped under one top-level tab.
// Same pattern as CHudSubOptionsRoot.
class CMultiplayerSubOptionsRoot : public vgui2::PropertySheet
{
public:
	DECLARE_CLASS_SIMPLE(CMultiplayerSubOptionsRoot, vgui2::PropertySheet);

	CMultiplayerSubOptionsRoot(vgui2::Panel *parent);

private:
	CChatSubOptions *m_pChat = nullptr;
	CScoreboardSubOptions *m_pScoreboard = nullptr;
	CModelSubOptions *m_pModels = nullptr;

	MESSAGE_FUNC(OnResetData, "ResetData");
	MESSAGE_FUNC(OnApplyChanges, "ApplyChanges");
};

#endif
