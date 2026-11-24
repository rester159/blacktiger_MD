#ifndef BOOT_LOGOS_H
#define BOOT_LOGOS_H
#include <genesis.h>
extern volatile u16 boot_stage,boot_tick;
extern volatile u8 boot_done;
void boot_logos(void);
/* Wait at most `frames` VBlanks for Start to be released, so a misread pad
   can never hold the boot on a black screen. */
void boot_wait_start_release(u16 frames);
/* Hardware diagnostic builds (EXTRA_FLAGS=-DBOOT_TRACE) paint the backdrop at
   each boot stage, so a tester can report where a black screen stops. */
#ifdef BOOT_TRACE
#define BOOT_TRACE_COLOR(c) do{PAL_setColor(0,(c));VDP_setBackgroundColor(0);}while(0)
#else
#define BOOT_TRACE_COLOR(c) do{}while(0)
#endif
#endif
