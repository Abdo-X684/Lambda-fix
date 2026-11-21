#ifndef OPTIONS_HUD_COLOR_H
#define OPTIONS_HUD_COLOR_H
#include <vgui_controls/PropertyPage.h>

class CCvarColor;
class CCvarCheckButton;

class CHudSubOptionsColors : public vgui2::PropertyPage
{
public:
	DECLARE_CLASS_SIMPLE(CHudSubOptionsColors, vgui2::PropertyPage);

	CHudSubOptionsColors(vgui2::Panel *parent);

	virtual void OnResetData();
	virtual void OnApplyChanges();

private:
	vgui2::Label *m_pColorLabel[5];
	CCvarColor *m_pColorValue[5];
	CCvarCheckButton *m_pColorOverride = nullptr;

	vgui2::Label *m_pSpeedColorLabel = nullptr;
	CCvarColor *m_pSpeedColorValue = nullptr;
	vgui2::Label *m_pArmorColorLabel = nullptr;
	CCvarColor *m_pArmorColorValue = nullptr;
	CCvarCheckButton *m_pArmorCustom = nullptr;
};

#endif
