
#include <windows.h>
struct CSysModule;
extern "C" void *__acrt_heap = nullptr;
CSysModule *Sys_LoadModule(const char *pModuleName)
{
    return (CSysModule *)LoadLibraryA(pModuleName);
}
