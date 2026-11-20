#ifndef CABOUTSUBOPTIONS_H
#define CABOUTSUBOPTIONS_H
#include <vgui_controls/PropertyPage.h>
#include "CGameVersion.h"

namespace vgui2
{
class Label;
class URLLabel;
}

class COptionsURLButton;

class CAboutSubOptions : public vgui2::PropertyPage
{
	DECLARE_CLASS_SIMPLE(CAboutSubOptions, vgui2::PropertyPage);

public:
	CAboutSubOptions(vgui2::Panel *parent);
	~CAboutSubOptions();
	virtual void ApplySchemeSettings(vgui2::IScheme *pScheme);
	virtual void PerformLayout();

private:
	vgui2::Label *m_pBHLLabel = nullptr;
	vgui2::Label *m_pVerTextLabel = nullptr;
	vgui2::Label *m_pVerLabel = nullptr;

	vgui2::URLLabel *m_pGitHubLink = nullptr;
	vgui2::URLLabel *m_pAghlLink = nullptr;
	COptionsURLButton *m_pOSSCredits = nullptr;

	CGameVersion m_GameVer;

	void UpdateControls();
};

#endif
