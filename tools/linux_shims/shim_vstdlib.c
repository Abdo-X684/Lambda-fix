/* Clean-room libvstdlib stand-in: provides RandomFloat only (the single vstdlib symbol the client imports). */
#include <stdlib.h>
float RandomFloat(float lo, float hi)
{
    return lo + (hi - lo) * ((float)rand() / (float)RAND_MAX);
}
