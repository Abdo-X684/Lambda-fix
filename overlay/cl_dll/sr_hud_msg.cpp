// BugfixedHL x Opposing Force - Speedrun Merge Kit
// Client handler for the server-authoritative split message.
#include "hud.h"
#include "cl_util.h"
#include "parsemsg.h"

#include "sr_core.h"
#include "sr_hud_msg.h"
#include "sr_hud_timer.h"

int __MsgFunc_SRSplit(const char* pszName, int iSize, void* pbuf) {
    (void)pszName;
    BEGIN_READ(pbuf, iSize);
    const int at = READ_LONG();
    const int delta = READ_LONG();
    const int hasPb = READ_BYTE();
    const char* map = READ_STRING();
    if (!READ_OK()) {
        return 0;
    }
    SR_HUD_OnSplit(map, static_cast<sr::Ms>(at), static_cast<sr::Ms>(delta), hasPb != 0);
    return 1;
}
