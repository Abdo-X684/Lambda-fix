#pragma once
// Minimal placement-new shim for the external StackWalker source. It is NOT
// used by the game DLL sources (they use the real libc++ <new>).
#include <stddef.h>
inline void *operator new(size_t, void *p) noexcept { return p; }
inline void *operator new[](size_t, void *p) noexcept { return p; }
inline void operator delete(void *, void *) noexcept {}
inline void operator delete[](void *, void *) noexcept {}
