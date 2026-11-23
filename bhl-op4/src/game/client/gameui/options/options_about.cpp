#include <string>
#include <vector>
#include <FileSystem.h>
#include <tier1/strtools.h>
#include <vgui/ILocalize.h>
#include <vgui_controls/Label.h>
#include <vgui_controls/URLLabel.h>
#include <vgui_controls/Frame.h>
#include <vgui_controls/RichText.h>
#include <KeyValues.h>
#include <appversion.h>
#include <bhl_urls.h>
#include "client_vgui.h"
#include "options_about.h"

class COptionsOSSCreditsDialog : public vgui2::Frame
{
public:
	DECLARE_CLASS_SIMPLE(COptionsOSSCreditsDialog, vgui2::Frame);

	COptionsOSSCreditsDialog(vgui2::Panel *pParent, const char *name)
	    : BaseClass(pParent, name)
	{
		SetTitle("#BHL_AdvOptions_About_OSSCredits", true);
		SetSize(640, 480);
		m_pText = new vgui2::RichText(this, "Text");

		// Fill m_pText with file contents
		FileHandle_t fh = g_pFullFileSystem->Open(VGUI2_ROOT_DIR "resource/open_source_software.txt", "r");

		if (fh == FILESYSTEM_INVALID_HANDLE)
		{
			Error("Failed to open open_source_software.txt");
			m_pText->SetText("Failed to open open_source_software.txt");
			return;
		}

		int size = g_pFullFileSystem->Size(fh);
		std::vector<char> buf(size + 1);
		size = g_pFullFileSystem->Read(buf.data(), size, fh);
		buf[size] = '\0';

		std::vector<wchar_t> wbuf(size + 1);
		Q_UTF8ToWString(buf.data(), wbuf.data(), wbuf.size() * sizeof(wchar_t));
		m_pText->SetText(wbuf.data());
	}

	virtual void PerformLayout() override
	{
		BaseClass::PerformLayout();

		int x, y, wide, tall;
		GetClientArea(x, y, wide, tall);
		m_pText->SetBounds(x, y, wide, tall);
	}

private:
	vgui2::RichText *m_pText = nullptr;
};

class COptionsURLButton : public vgui2::URLLabel
{
public:
	DECLARE_CLASS_SIMPLE(COptionsURLButton, vgui2::URLLabel);

	COptionsURLButton(vgui2::Panel *pParent, const char *name, const char *text)
	    : BaseClass(pParent, name, text, "")
	{
	}

	virtual void OnMousePressed(vgui2::MouseCode code) override
	{
		if (code == vgui2::MOUSE_LEFT)
		{
			if (!m_pDialog)
				m_pDialog = new COptionsOSSCreditsDialog(this, "OSSCreditsDialog");

			m_pDialog->MoveToCenterOfScreen();
			m_pDialog->Activate();
		}
	}

private:
	COptionsOSSCreditsDialog *m_pDialog = nullptr;
};

CAboutSubOptions::CAboutSubOptions(vgui2::Panel *parent)
    : BaseClass(parent, "AboutSubOptions")
{
	SetSize(100, 100); // Silence "parent not sized yet" warning

	m_pBHLLabel = new vgui2::Label(this, "BHLLabel", "#BHL_AdvOptions_About_BHL");
	m_pVerTextLabel = new vgui2::Label(this, "VerTextLabel", "#BHL_AdvOptions_About_Version");
	m_pVerLabel = new vgui2::Label(this, "VerLabel", "?");

	m_pGitHubLink = new vgui2::URLLabel(this, "GitHubLink", "#BHL_AdvOptions_About_GitHub", "URL goes here");
	m_pAghlLink = new vgui2::URLLabel(this, "AghlLink", "#BHL_AdvOptions_About_AGHL", "URL goes here");
	m_pOSSCredits = new COptionsURLButton(this, "OSSCredits", "#BHL_AdvOptions_About_OSSCredits");

	m_GameVer = CGameVersion(APP_VERSION);

	LoadControlSettings(VGUI2_ROOT_DIR "resource/options/AboutSubOptions.res");
}

CAboutSubOptions::~CAboutSubOptions()
{
}

void CAboutSubOptions::ApplySchemeSettings(vgui2::IScheme *pScheme)
{
	BaseClass::ApplySchemeSettings(pScheme);
}

void CAboutSubOptions::PerformLayout()
{
	BaseClass::PerformLayout();

	m_pGitHubLink->SetURL("https://github.com/Abdo-X684/Lambda-fix"); // Lambda fix repository
	m_pAghlLink->SetURL(BHL_FORUM_URL);

	auto fnPositionAfter = [](vgui2::Label *left, vgui2::Label *right) {
		int x, y, wide, tall;
		left->GetPos(x, y);
		left->GetContentSize(wide, tall);
		left->SetWide(wide);
		right->SetPos(x + wide, y);
	};

	fnPositionAfter(m_pVerTextLabel, m_pVerLabel);

	UpdateControls();
}

void CAboutSubOptions::UpdateControls()
{
	char buf[128];
	wchar_t wbuf[128];

	// Update client's version
	{
		// Show only the release number, e.g. "1.0.0"
		snprintf(buf, sizeof(buf), "%d.%d.%d", m_GameVer.GetMajor(), m_GameVer.GetMinor(), m_GameVer.GetPatch());
		std::string gameVer = buf;
		gameVer += " stable";

#ifdef _DEBUG
		gameVer += " [Debug build]";
#endif

		g_pVGuiLocalize->ConvertANSIToUnicode(gameVer.c_str(), wbuf, sizeof(wbuf));
		m_pVerLabel->SetText(wbuf);
	}
}
