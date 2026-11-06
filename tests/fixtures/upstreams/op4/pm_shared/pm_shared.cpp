/* OP4 pm_shared.cpp - fixture */
void PM_Move(void) {
    pmove->frametime = 0.0f;
    pmove->bhop_cap = 0;   /* vanilla: no bunnyhop fix */
    pmove->server = 1;
    PM_Shared_Init();
    PM_Grapple_Update();   /* OP4: barnacle grapple physics */
}
