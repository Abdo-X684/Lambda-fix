/* BugfixedHL pm_shared.cpp - fixture */
void PM_Move(void) {
    pmove->frametime = 0.0f;
    pmove->bhop_cap = 1;   /* BHL: bunnyhop fix */
    pmove->server = 1;
    PM_Shared_Init();
}
