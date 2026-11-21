#include <exception>
#include <string>
#include <fstream>
#include <sstream>

#include <appversion.h>
#include "bhlcfg.h"
#include "hud.h"
#include "cl_util.h"

#define BHL_CONFIG_NAME       "bugfixedhl.cfg"
#define BHL_CONFIG_USER_BEGIN "// [USER CONFIG BEGIN - DO NOT EDIT THIS LINE]"

namespace bhlcfg
{
static void SaveConfig(const char *cfgname);
}

// Version of the OP4 color defaults applied by lambda_apply_defaults.
// Saved to bugfixedhl.cfg, so the reset runs once per install.
static ConVar lambda_defaults_version("lambda_defaults_version", "0", FCVAR_BHL_ARCHIVE,
	"Version of the applied OP4 color defaults (internal)");

// Sets the main HUD color, HUD number coloring, and crosshair color to the
// original Opposing Force green (0 160 0). Runs after bugfixedhl.cfg is loaded,
// so older saved values are replaced once.
static void ApplyColorDefaults()
{
	const int kVersion = 1;
	if (lambda_defaults_version.GetInt() >= kVersion)
		return;

	gEngfuncs.Cvar_Set("hud_color", "0 160 0");
	gEngfuncs.Cvar_Set("hud_color_override", "1");
	gEngfuncs.Cvar_SetValue("cl_cross_red", 0);
	gEngfuncs.Cvar_SetValue("cl_cross_green", 160);
	gEngfuncs.Cvar_SetValue("cl_cross_blue", 0);
	lambda_defaults_version.SetValue(kVersion);
}

void bhlcfg::Init()
{
	gEngfuncs.pfnAddCommand("lambda_apply_defaults", ApplyColorDefaults);
	gEngfuncs.pfnClientCmd("exec " BHL_CONFIG_NAME);
	gEngfuncs.pfnClientCmd("lambda_apply_defaults");
	// Cheats stay off at every start. Turn them on only for a test session.
	gEngfuncs.pfnClientCmd("sv_cheats 0");
}

void bhlcfg::Shutdown()
{
	try
	{
		SaveConfig(BHL_CONFIG_NAME);
	}
	catch (const std::exception &)
	{
		// Ignore. Nothing we can do at this point.
	}
}

void bhlcfg::SaveConfig(const char *cfgname)
{
	char filename[256];
	snprintf(filename, sizeof(filename), "%s/%s", gEngfuncs.pfnGetGameDirectory(), cfgname);

	std::fstream file;

	// Read user config
	file.open(filename, std::fstream::in);
	std::string userCfg;

	if (!file.fail()) // Open may fail if file doesn't exist
	{
		std::string line;
		bool isBeginFound = false;
		while (std::getline(file, line))
		{
			if (isBeginFound)
			{
				userCfg += line + "\n";
			}
			else
			{
				if (line == BHL_CONFIG_USER_BEGIN)
					isBeginFound = true;
			}
		}
	}

	file.close();
	file.clear();

	// Save new config
	file.open(filename, std::fstream::out);
	if (file.fail())
	{
		std::stringstream s;
		s << "failed to save config file " << filename << ". errno = " << errno << " [" << strerror(errno) << "]";
		throw std::runtime_error(s.str());
	}

	// Header
	file << "// BugfixedHL v" << APP_VERSION << " config file\n";
	file << "// The first part is generated automatically.\n";
	file << "// The second part can be modified manually.\n";
	file << "// Look for a huge block of comments below.\n";
	file << "\n";

	// Cvars
	for (cvar_t *i = gEngfuncs.GetFirstCvarPtr(); i; i = i->next)
	{
		if (i->flags & FCVAR_BHL_ARCHIVE)
		{
			file << i->name << " \"" << i->string << "\"\n";
		}
	}

	// User commands
	file << "\n\n";
	file << "// You can add your own commands below.\n";
	file << "// It works just like userconfig.cfg, but will only be executed on BugfixedHL clients.\n";
	file << "// It is recomended to add your custom commands to a separate\n";
	file << "// config file and execute it here like this:\n";
	file << "//     exec myconfigname.cfg\n";
	file << "// That way you won't lose your config if this file was damaged\n";
	file << "// and subsequently overwritten.\n";
	file << "// DO NOT TOUCH line just next to this one.\n";
	file << BHL_CONFIG_USER_BEGIN << "\n";
	file << userCfg;
}
