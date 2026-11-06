// ---------------------------------------------------------------------
// Source: BugfixedHL-Rebased src/game/client/bhlcfg.cpp (GPL-3.0-or-later).
// Ported INTO the OP4 client DLL with these COMPAT changes only:
//   * appversion.h (CMake-generated, absent from the OP4 tree) -> BHL_MERGE_VERSION
//   * try/catch removed: the OP4 Linux build uses -fno-exceptions
//   * includes go through bhl_compat.h (BHL's modern cl_dll.h is not present)
// Everything else -- bugfixedhl.cfg, FCVAR_BHL_ARCHIVE persistence and the
// [USER CONFIG BEGIN] section -- is BHL's own system, unchanged.
// ---------------------------------------------------------------------
#include "bhl_compat.h"

#include <fstream>
#include <sstream>
#include <string>

#include "bhlcfg.h"

#define BHL_CONFIG_NAME       "bugfixedhl.cfg"
#define BHL_CONFIG_USER_BEGIN "// [USER CONFIG BEGIN - DO NOT EDIT THIS LINE]"

namespace bhlcfg {
static void SaveConfig(const char* cfgname);
}

void bhlcfg::Init()
{
    gEngfuncs.pfnClientCmd("exec " BHL_CONFIG_NAME);
}

void bhlcfg::Shutdown()
{
    // COMPAT: no exceptions in the GoldSrc build.
    SaveConfig(BHL_CONFIG_NAME);
}

void bhlcfg::SaveConfig(const char* cfgname)
{
    char filename[256];
    std::snprintf(filename, sizeof(filename), "%s/%s",
                  gEngfuncs.pfnGetGameDirectory(), cfgname);

    std::fstream file;
    std::string userCfg;

    // Read the user-editable tail of the existing config.
    file.open(filename, std::fstream::in);
    if (!file.fail())
    {
        std::string line;
        bool isBeginFound = false;
        while (std::getline(file, line))
        {
            if (isBeginFound)
                userCfg += line + "\n";
            else if (line == BHL_CONFIG_USER_BEGIN)
                isBeginFound = true;
        }
    }
    file.close();
    file.clear();

    file.open(filename, std::fstream::out);
    if (file.fail())
        return;  // COMPAT: was throw std::runtime_error(...)

    file << "// BugfixedHL (merged into Opposing Force) " << BHL_MERGE_VERSION << " config file\n";
    file << "// The first part is generated automatically.\n";
    file << "// The second part can be modified manually.\n";
    file << "\n";

    // BHL's own cvar system: every FCVAR_BHL_ARCHIVE cvar is written here.
    for (cvar_t* i = gEngfuncs.GetFirstCvarPtr(); i; i = i->next)
    {
        if (i->flags & FCVAR_BHL_ARCHIVE)
            file << i->name << " \"" << i->string << "\"\n";
    }

    file << "\n\n";
    file << "// You can add your own commands below.\n";
    file << "// It works just like userconfig.cfg, but will only be executed on BugfixedHL clients.\n";
    file << "// DO NOT TOUCH line just next to this one.\n";
    file << BHL_CONFIG_USER_BEGIN << "\n";
    file << userCfg;
}
