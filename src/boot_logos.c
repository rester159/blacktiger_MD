#include "boot_logos.h"
/* Source-only startup. The original Black Tiger game intro is retained;
   no Sonic PCM, Shinobi graphics or Street Fighter logo data is embedded.
   A local build that has the private kit in src/private_boot/ (gitignored) links
   boot_logos_private(), which shows the SEGA and CAPCOM logos instead. */
void boot_logos_private(void) __attribute__((weak));
volatile u16 boot_stage,boot_tick;
volatile u8 boot_done;
void boot_wait_start_release(u16 frames) {
    while(frames-- && (JOY_readJoypad(JOY_1)&BUTTON_START))SYS_doVBlankProcess();
}
void boot_logos(void) {
    if (boot_logos_private) { boot_logos_private(); return; }
    boot_stage=0;boot_tick=0;boot_done=0;
    VDP_setEnable(FALSE);
    boot_stage=1;
    for(boot_tick=0;boot_tick<4;boot_tick++)SYS_doVBlankProcess();
    boot_wait_start_release(180);
    boot_stage=3;boot_done=1;
}
