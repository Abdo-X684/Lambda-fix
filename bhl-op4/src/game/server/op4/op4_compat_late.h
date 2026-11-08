/* ---------------------------------------------------------------------------
 * Late compatibility macros. Included AFTER an OP4 source's own #include
 * block, so they cannot corrupt BHL header declarations (a macro named
 * FindHullIntersection would otherwise expand inside weapons.h).
 * -------------------------------------------------------------------------*/
#ifndef OP4_BHL_COMPAT_LATE_H
#define OP4_BHL_COMPAT_LATE_H
#include "op4_compat.h"

#include "op4_entity_enumerator.h"

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

  /* OP4's Vector::Make2D() (OP4 dlls/vector.h:115) returns Vector2D{x,y};
   * BHL's Source-SDK mathlib Vector spells that AsVector2D() (vector.h:113).
   * Mechanical member-name mapping only; the expression is unchanged. */
  #ifndef OP4_BHL_NO_MAKE2D_MACRO
  #define Make2D() AsVector2D()
  #endif

  /* OP4 dlls/explode.h:25 has a 5-arg ExplosionCreate(center, angles,
   * pOwner, magnitude, doDamage). BHL's explode.h:28 additionally separates
   * pInflictor from pAttacker. OP4 passes one owner for both roles, so this
   * inline forwards to BHL's real ExplosionCreate with that mapping. The
   * declaration is repeated so the overload is available even in TUs that
   * never include explode.h; no function body is replaced or invented. */
  extern void ExplosionCreate(const Vector &center, const Vector &angles,
                              edict_t *pInflictor, edict_t *pAttacker,
                              int magnitude, BOOL doDamage);
  inline void ExplosionCreate(const Vector &center, const Vector &angles,
                              edict_t *pOwner, int magnitude, bool doDamage)
  {
      ::ExplosionCreate(center, angles, pOwner, pOwner, magnitude, doDamage ? 1 : 0);
  }
  #endif /* OP4_BHL_COMPAT_LATE_H */
  