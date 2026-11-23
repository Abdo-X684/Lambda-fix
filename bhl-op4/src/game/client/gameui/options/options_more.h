#ifndef CMORESUBOPTIONS_H
#define CMORESUBOPTIONS_H
#include <vgui_controls/PropertyPage.h>

namespace vgui2
{
class Label;
}

class CCvarCheckButton;
class CCvarTextEntry;

// "More options" page under the Multiplayer tab. Holds the options that were
// previously on the General page: HTML MOTD, chat logging, demo recording.
class CMoreSubOptions : public vgui2::PropertyPage
{
	DECLARE_CLASS_SIMPLE(CMoreSubOptions, vgui2::PropertyPage);

public:
	CMoreSubOptions(vgui2::Panel *parent);

	virtual void OnResetData();
	virtual void OnApplyChanges();

private:
	CCvarCheckButton *m_pMOTD = nullptr;
	vgui2::Label *m_pMOTDLabel = nullptr;

	CCvarCheckButton *m_pLogChat = nullptr;
	CCvarCheckButton *m_pLogOther = nullptr;
	CCvarCheckButton *m_pAutoDemo = nullptr;
	vgui2::Label *m_pAutoDemoLabel = nullptr;
	CCvarTextEntry *m_pKeepFor = nullptr;
	vgui2::Label *m_pKeepForLabel = nullptr;
	vgui2::Label *m_pDaysLabel = nullptr;
};

#endif
