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

  /* ---- OP4 dlls/player.h:473-602, verbatim --------------------------- *
   * Only compiled where BHL's player.h has already been included (guard
   * PLAYER_H), because CPlayerIterator needs CBasePlayer complete. OP4's
   * CTF rules iterate players with UTIL_FindPlayers(); BHL exposes only
   * UTIL_PlayerByIndex(), which is exactly what this adapter calls.       */
  #ifdef PLAYER_H
  class CPlayerIterator
  {
  public:
      static const int FirstPlayerIndex = 1;

      CPlayerIterator()
          : m_pPlayer(nullptr), m_iNextIndex(gpGlobals->maxClients + 1)
      {
      }

      CPlayerIterator(const CPlayerIterator&) = default;

      CPlayerIterator(CBasePlayer* pPlayer)
          : m_pPlayer(pPlayer), m_iNextIndex(pPlayer ? pPlayer->entindex() + 1 : FirstPlayerIndex)
      {
      }

      CPlayerIterator& operator=(const CPlayerIterator&) = default;

      const CBasePlayer* operator*() const { return m_pPlayer; }

      CBasePlayer* operator*() { return m_pPlayer; }

      CBasePlayer* operator->() { return m_pPlayer; }

      void operator++()
      {
          m_pPlayer = static_cast<CBasePlayer*>(FindNextPlayer(m_iNextIndex, &m_iNextIndex));
      }

      void operator++(int)
      {
          ++*this;
      }

      bool operator==(const CPlayerIterator& other) const
      {
          return m_pPlayer == other.m_pPlayer;
      }

      bool operator!=(const CPlayerIterator& other) const
      {
          return !(*this == other);
      }

      static CBasePlayer* FindNextPlayer(int index, int* pOutNextIndex = nullptr)
      {
          while (index <= gpGlobals->maxClients)
          {
              auto pPlayer = UTIL_PlayerByIndex(index);

              if (pPlayer)
              {
                  if (pOutNextIndex)
                  {
                      *pOutNextIndex = index + 1;
                  }

                  return static_cast<CBasePlayer*>(pPlayer);
              }

              ++index;
          }

          if (pOutNextIndex)
          {
              *pOutNextIndex = gpGlobals->maxClients;
          }

          return nullptr;
      }

  private:
      int m_iNextIndex = 1;
      CBasePlayer* m_pPlayer;
  };

  class CPlayerEnumerator
  {
  public:
      using iterator = CPlayerIterator;

      CPlayerEnumerator() = default;

      iterator begin()
      {
          return {static_cast<CBasePlayer*>(CPlayerIterator::FindNextPlayer(CPlayerIterator::FirstPlayerIndex))};
      }

      iterator end()
      {
          return {};
      }
  };

  class CPlayerEnumeratorWithStart
  {
  public:
      using iterator = CPlayerIterator;

      CPlayerEnumeratorWithStart(CBasePlayer* pStartEntity)
          : m_pStartEntity(pStartEntity)
      {
      }

      iterator begin()
      {
          return {m_pStartEntity};
      }

      iterator end()
      {
          return {};
      }

  private:
      CBasePlayer* m_pStartEntity = nullptr;
  };

  inline CPlayerEnumerator UTIL_FindPlayers()
  {
      return {};
  }

  inline CPlayerEnumeratorWithStart UTIL_FindPlayers(CBasePlayer* pStartEntity)
  {
      return {pStartEntity};
  }
  #endif /* PLAYER_H */
  #endif /* OP4_BHL_COMPAT_LATE_H */
  