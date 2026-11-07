/* ---------------------------------------------------------------------------
 * Late compatibility macros. Included AFTER an OP4 source's own #include
 * block, so they cannot corrupt BHL header declarations (a macro named
 * FindHullIntersection would otherwise expand inside weapons.h).
 * -------------------------------------------------------------------------*/
#ifndef OP4_BHL_COMPAT_LATE_H
#define OP4_BHL_COMPAT_LATE_H
#include "op4_compat.h"

/* BHL: PLAYBACK_EVENT_FULL is (*g_engfuncs.pfnPlaybackEvent), float* args.
 * OP4: passes Vector origin/angles. */
#undef PLAYBACK_EVENT_FULL
#define PLAYBACK_EVENT_FULL(flags, pInvoker, eventindex, delay, origin, angles, fparam1, fparam2, iparam1, iparam2, bparam1, bparam2) \
	(*g_engfuncs.pfnPlaybackEvent)(flags, pInvoker, eventindex, delay, OP4_VEC(origin), OP4_VEC(angles), fparam1, fparam2, iparam1, iparam2, bparam1, bparam2)

/* BHL's FindHullIntersection takes float* hull bounds; OP4 passes Vector. */
#define FindHullIntersection(src, tr, mins, maxs, ent) \
	FindHullIntersection(src, tr, OP4_VEC(mins), OP4_VEC(maxs), ent)

/* OP4's Vector::Normalize() returns a normalised copy; BHL's mathlib Vector
 * spells that Normalized(). This macro is defined only after all headers have
 * been parsed (see file header), so it cannot change BHL declarations. */
#ifndef OP4_BHL_NO_NORMALIZE_MACRO
#define Normalize() Normalized()
#endif
#endif /* OP4_BHL_COMPAT_LATE_H */
