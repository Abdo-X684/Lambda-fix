#pragma once
// On MSVC this header hides Windows' HSPRITE typedef behind a macro so the
// engine's `typedef int HSPRITE` does not clash. clang needs it unconditionally.
#ifdef HSPRITE
#undef HSPRITE
#endif
#define HSPRITE WINDOWS_HSPRITE
