/* OP4 pm_shared.cpp - fixture with the OP4-native bunnyhop implementation */
#define BUNNYJUMP_MAX_SPEED_FACTOR 1.7f

void PM_PreventMegaBunnyJumping()
{
	const bool allowBunnyHopping = atoi(PM_Info_ValueForKey(pmove->physinfo, "bj")) == 1;
	if (allowBunnyHopping)
		return;
	const float maxscaledspeed = BUNNYJUMP_MAX_SPEED_FACTOR * pmove->maxspeed;
	(void)maxscaledspeed;
}

void PM_Jump()
{
	PM_PreventMegaBunnyJumping();
	PM_Grapple_Update();   /* OP4: barnacle grapple physics */
}
