/* Clean-room replacement for the tier0/vstdlib symbols the BHL client imports.
 * Written from the symbol list only; no Valve code is copied.
 * Names are C-linkage because the client imports them unmangled. */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ---- ICommandLine: vtable order follows the public interface (12 slots) ---- */
static char g_cmdline[4096];
static char *g_argv[256];
static int g_argc;

static void cl_build_from_proc(void)
{
    FILE *f = fopen("/proc/self/cmdline", "rb");
    size_t n = 0;
    if (!f) return;
    n = fread(g_cmdline, 1, sizeof(g_cmdline) - 1, f);
    fclose(f);
    g_cmdline[n] = 0;
    g_argc = 0;
    for (size_t i = 0; i < n && g_argc < 255;) {
        g_argv[g_argc++] = &g_cmdline[i];
        i += strlen(&g_cmdline[i]) + 1;
    }
    g_argv[g_argc] = NULL;
}

static void cl_create1(void *self, const char *s) { (void)self; (void)s; }
static void cl_create2(void *self, int argc, char **argv) { (void)self; (void)argc; (void)argv; }
static const char *cl_getcmdline(const void *self) { (void)self; return g_cmdline; }
static const char *cl_checkparm(const void *self, const char *psz, const char **ppszValue)
{
    int i;
    (void)self;
    for (i = 1; i < g_argc; i++) {
        if (strcmp(g_argv[i], psz) == 0) {
            if (ppszValue) *ppszValue = (i + 1 < g_argc) ? g_argv[i + 1] : NULL;
            return g_argv[i];
        }
    }
    if (ppszValue) *ppszValue = NULL;
    return NULL;
}
static void cl_removeparm(void *self, const char *parm) { (void)self; (void)parm; }
static void cl_appendparm(void *self, const char *p, const char *v) { (void)self; (void)p; (void)v; }
static const char *cl_parmvalue_s(const void *self, const char *psz, const char *def)
{
    const char *v = NULL;
    (void)self;
    if (cl_checkparm(self, psz, &v) && v) return v;
    return def;
}
static int cl_parmvalue_i(const void *self, const char *psz, int def)
{
    const char *v = NULL;
    (void)self;
    if (cl_checkparm(self, psz, &v) && v) return atoi(v);
    return def;
}
static float cl_parmvalue_f(const void *self, const char *psz, float def)
{
    const char *v = NULL;
    (void)self;
    if (cl_checkparm(self, psz, &v) && v) return (float)atof(v);
    return def;
}
static int cl_parmcount(const void *self) { (void)self; return g_argc; }
static int cl_findparm(const void *self, const char *psz)
{
    int i;
    (void)self;
    for (i = 1; i < g_argc; i++) if (strcmp(g_argv[i], psz) == 0) return i;
    return 0;
}
static const char *cl_getparm(const void *self, int i)
{
    (void)self;
    return (i >= 0 && i < g_argc) ? g_argv[i] : "";
}

static void *cl_vtbl[] = {
    (void *)cl_create1, (void *)cl_create2, (void *)cl_getcmdline,
    (void *)cl_checkparm, (void *)cl_removeparm, (void *)cl_appendparm,
    (void *)cl_parmvalue_s, (void *)cl_parmvalue_i, (void *)cl_parmvalue_f,
    (void *)cl_parmcount, (void *)cl_findparm, (void *)cl_getparm,
};
static struct { void **vptr; } g_commandline = { cl_vtbl };

void *CommandLine(void)
{
    static int inited = 0;
    if (!inited) { cl_build_from_proc(); inited = 1; }
    return &g_commandline;
}

/* ---- logging: write to stderr; the engine console is not reachable from here ---- */
void Msg(const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vfprintf(stdout, fmt, ap); va_end(ap); fflush(stdout);
}
void Warning(const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vfprintf(stderr, fmt, ap); va_end(ap);
}
void Error(const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vfprintf(stderr, fmt, ap); va_end(ap);
    abort();
}

/* ---- timing / random ---- */
double Plat_FloatTime(void)
{
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

/* ---- assert / spew: minimal, non-fatal ---- */
int AssertValidStringPtr(const char *p, int maxchar) { (void)maxchar; return p != NULL; }
int _AssertValidReadPtr(void *p, int count) { (void)count; return p != NULL; }
int _AssertValidWritePtr(void *p, int count) { (void)count; return p != NULL; }
int ShouldUseNewAssertDialog(void) { return 0; }
int DoNewAssertDialog(const char *f, int l, const char *e) { (void)f; (void)l; (void)e; return 0; }
void _ExitOnFatalAssert(const char *f, int l) { (void)f; (void)l; abort(); }
void _SpewInfo(int type, const char *f, int l) { (void)type; (void)f; (void)l; }
int _SpewMessage(const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vfprintf(stderr, fmt, ap); va_end(ap);
    return 0; /* SPEW_CONTINUE */
}
static void *g_spew_fn;
void SpewOutputFunc(void *fn) { g_spew_fn = fn; }
void *GetSpewOutputFunc(void) { return g_spew_fn; }

/* ---- pcre table: zeroed (regex character classes will be wrong; see README) ---- */
unsigned char _pcre_default_tables[1088];
