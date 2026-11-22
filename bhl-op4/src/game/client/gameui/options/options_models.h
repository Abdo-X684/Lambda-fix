#ifndef OPTIONS_MODELS_H
#define OPTIONS_MODELS_H
#include <vector>
#include <vgui_controls/PropertyPage.h>

namespace vgui2
{
class Button;
class ListPanel;
class ScrollBar;
class TextEntry;
}

class CCvarCheckButton;
class CCvarTextEntry;

class CModelSubOptions : public vgui2::PropertyPage
{
public:
	DECLARE_CLASS_SIMPLE(CModelSubOptions, vgui2::PropertyPage);

	CModelSubOptions(vgui2::Panel *parent);

	void OnCommand(const char *cmd) override;
	void OnResetData() override;
	void OnApplyChanges() override;
	void PerformLayout() override;
	void OnMouseWheeled(int delta) override;
	MESSAGE_FUNC_INT(OnScrollBarMoved, "ScrollBarSliderMoved", position);

private:
	vgui2::ListPanel *m_pEnemyModels = nullptr;
	vgui2::Button *m_pAddEnemyModel = nullptr;
	vgui2::Button *m_pRemoveEnemyModel = nullptr;
	vgui2::Button *m_pRemoveAllEnemyModels = nullptr;
	vgui2::TextEntry *m_pNewEnemyModelName = nullptr;

	CCvarTextEntry *m_pTeamModel = nullptr;
	CCvarTextEntry *m_pEnemyColors = nullptr;
	CCvarTextEntry *m_pTeamColors = nullptr;
	CCvarCheckButton *m_pHideCorpses = nullptr;
	CCvarCheckButton *m_pLeftHand = nullptr;
	CCvarCheckButton *m_pAngledBob = nullptr;
	CCvarCheckButton *m_pNoShells = nullptr;
	CCvarCheckButton *m_pNoViewModel = nullptr;

	int m_iNewItemIdx = 0;

	// The page is taller than the sheet area: a scrollbar on the right moves the controls up.
	struct ScrollChild
	{
		vgui2::Panel *panel;
		int x;
		int y;
	};
	std::vector<ScrollChild> m_ScrollChildren;
	vgui2::ScrollBar *m_pScrollBar = nullptr;
	int m_iContentTall = 0;
	int m_iScrollOffset = 0;

	int GetScrollRange() const;
	void UpdateScrollOffset();

	void ParseEnemyModels();
	void ApplyEnemyModels();
};

#endif
