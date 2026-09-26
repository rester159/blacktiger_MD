#include "boot_logos.h"
/* Source-only startup. The original Black Tiger game intro is retained;
   no Sonic PCM, Shinobi graphics or Street Fighter logo data is embedded. */
volatile u16 boot_stage,boot_tick;
volatile u8 boot_done;
void boot_logos(void) {
    boot_stage=0;boot_tick=0;boot_done=0;
    VDP_setEnable(FALSE);
    boot_stage=1;
    for(boot_tick=0;boot_tick<4;boot_tick++)SYS_doVBlankProcess();
    while(JOY_readJoypad(JOY_1)&BUTTON_START)SYS_doVBlankProcess();
    boot_stage=3;boot_done=1;
}
