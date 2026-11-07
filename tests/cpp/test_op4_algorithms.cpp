/*
 * Executable functional tests for two REAL OP4 algorithms that the BHL-root
 * build compiles into client.so / hl.so.
 *
 * These are NOT stubs and NOT a simulation of the game: the test includes the
 * exact headers shipped in bhl-op4/ and executes the same C++ statements that
 * the delivered ELF32 libraries execute.
 *
 *   1. OP4_ComputeNextAttackDelay  (bhl-op4/src/game/shared/op4_weapon_timing.h)
 *      == halflife-op4-updated dlls/weapons.cpp:1069-1099
 *   2. UTIL_FindEntitiesByClassname / UTIL_FindEntitiesByTargetname
 *      (bhl-op4/src/game/server/op4/op4_entity_enumerator.h, included by
 *       op4_compat_late.h into every OP4 translation unit)
 *      == halflife-op4-updated dlls/util.h:597-735
 *
 * The host-side BHL types used by those headers are mocked at the top of this
 * file. No engine state is faked into the *result*: the assertions check the
 * numerical and iteration behaviour of the real OP4 statements themselves.
 *
 * In-game Opposing Force behaviour can NOT be tested this way; see
 * build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md.
 */

#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

/* ---- minimal host mocks of the BHL declarations the two headers need ---- */
struct CBaseEntity
{
	int id = 0;
	const char *classname = "";
	const char *targetname = "";
	virtual ~CBaseEntity() = default;
};

struct MockEntity : CBaseEntity
{
	int goalNum = 0;
};

static std::vector<MockEntity> g_byClass;
static std::vector<MockEntity> g_byTarget;

static CBaseEntity *nextAfter(const std::vector<MockEntity> &list,
							  CBaseEntity *start, const char *name, bool byClass)
{
	std::size_t i = 0;
	if (start)
	{
		for (i = 0; i < list.size(); ++i)
		{
			if (&list[i] == start)
			{
				++i;
				break;
			}
		}
	}
	for (; i < list.size(); ++i)
	{
		const char *key = byClass ? list[i].classname : list[i].targetname;
		if (name && key && std::strcmp(key, name) == 0)
			return const_cast<MockEntity *>(&list[i]);
	}
	return nullptr;
}

CBaseEntity *UTIL_FindEntityByClassname(CBaseEntity *start, const char *name)
{
	return nextAfter(g_byClass, start, name, true);
}

CBaseEntity *UTIL_FindEntityByTargetname(CBaseEntity *start, const char *name)
{
	return nextAfter(g_byTarget, start, name, false);
}

#include "../../bhl-op4/src/game/shared/op4_weapon_timing.h"
#include "../../bhl-op4/src/game/server/op4/op4_entity_enumerator.h"

static int g_failures = 0;

static void check(bool ok, const char *what)
{
	std::printf("  [%s] %s\n", ok ? "PASS" : "FAIL", what);
	if (!ok)
		++g_failures;
}

static bool near(float a, float b)
{
	return std::fabs(a - b) < 1e-4f;
}

static void test_GetNextAttackDelay()
{
	std::puts("OP4 dlls/weapons.cpp:1069-1099 GetNextAttackDelay:");

	/* First shot: bookkeeping resets, no creep. */
	OP4AttackTimingState s1;
	const float r1 = OP4_ComputeNextAttackDelay(0.5f, 10.0f, 10.0f, s1);
	check(near(r1, 10.5f), "first shot returns timeBase + delay (10.5)");
	check(near(s1.lastFireTime, 10.0f), "first shot stores lastFireTime");
	check(near(s1.prevPrimaryAttack, 0.5f), "first shot stores prevPrimaryAttack");

	/* Firing faster than the cyclic rate: negative creep pushes the next shot
	 * later than timeBase + delay. */
	OP4AttackTimingState s2;
	s2.nextPrimaryAttack = 10.5f;
	s2.prevPrimaryAttack = 0.5f;
	s2.lastFireTime = 10.0f;
	const float r2 = OP4_ComputeNextAttackDelay(0.5f, 10.1f, 10.1f, s2);
	check(near(r2, 11.0f), "rapid fire: negative creep (-0.4) -> 11.0");
	check(near(s2.prevPrimaryAttack, 0.9f), "rapid fire: prevPrimaryAttack = 0.9");

	/* Firing slower than the cyclic rate: positive creep. */
	OP4AttackTimingState s3;
	s3.nextPrimaryAttack = 11.0f;
	s3.prevPrimaryAttack = 0.9f;
	s3.lastFireTime = 10.1f;
	const float r3 = OP4_ComputeNextAttackDelay(0.5f, 11.5f, 11.5f, s3);
	check(near(r3, 11.5f), "slow fire: positive creep (+0.5) -> 11.5");
	check(near(s3.prevPrimaryAttack, 0.0f), "slow fire: prevPrimaryAttack = 0.0");

	/* m_flNextPrimaryAttack == -1 is OP4's "client stopped firing" reset. */
	OP4AttackTimingState s4;
	s4.nextPrimaryAttack = -1.0f;
	s4.prevPrimaryAttack = 7.0f;
	s4.lastFireTime = 3.0f;
	const float r4 = OP4_ComputeNextAttackDelay(0.25f, 20.0f, 20.0f, s4);
	check(near(r4, 20.25f), "client-stopped reset ignores stale prevPrimaryAttack");
	check(near(s4.lastFireTime, 20.0f), "reset stores lastFireTime");
	check(near(s4.prevPrimaryAttack, 0.25f), "reset stores prevPrimaryAttack");
}

static void test_EntityEnumerator()
{
	std::puts("OP4 dlls/util.h:597-735 UTIL_FindEntitiesByClassname:");

	g_byClass.clear();
	g_byClass.resize(5);
	for (int i = 0; i < 5; ++i)
	{
		g_byClass[i].id = i;
		g_byClass[i].classname = (i % 2 == 0) ? "item_ctfflag" : "item_ctfbase";
		g_byClass[i].goalNum = i + 1;
	}

	std::vector<int> ids;
	for (auto entity : UTIL_FindEntitiesByClassname<MockEntity>("item_ctfflag"))
		ids.push_back(entity->id);
	check(ids == std::vector<int>({0, 2, 4}),
		  "enumerates every matching classname in order (0,2,4)");

	std::vector<int> none;
	for (auto entity : UTIL_FindEntitiesByClassname<MockEntity>("does_not_exist"))
		none.push_back(entity->id);
	check(none.empty(), "no match yields an empty range");

	/* OP4's CTFGoalFlag::DisplayFlagStatus uses the start-entity overload. */
	MockEntity *start = &g_byClass[0];
	std::vector<int> afterStart;
	for (auto entity : UTIL_FindEntitiesByClassname<MockEntity>("item_ctfflag", start))
		afterStart.push_back(entity->id);
	check(afterStart == std::vector<int>({2, 4}),
		  "start-entity overload resumes after the given entity");

	g_byTarget.clear();
	g_byTarget.resize(3);
	for (int i = 0; i < 3; ++i)
	{
		g_byTarget[i].id = 100 + i;
		g_byTarget[i].targetname = (i == 1) ? "other" : "ctf_base";
	}
	std::vector<int> targets;
	for (auto entity : UTIL_FindEntitiesByTargetname<MockEntity>("ctf_base"))
		targets.push_back(entity->id);
	check(targets == std::vector<int>({100, 102}),
		  "targetname enumerator filters correctly");
}

int main()
{
	std::puts("== real OP4 algorithm functional tests ==");
	test_GetNextAttackDelay();
	test_EntityEnumerator();
	if (g_failures)
	{
		std::printf("== %d FAILURE(S) ==\n", g_failures);
		return 1;
	}
	std::puts("== ALL OP4 ALGORITHM TESTS PASSED ==");
	return 0;
}
