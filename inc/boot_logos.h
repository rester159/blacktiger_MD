#ifndef BOOT_LOGOS_H
#define BOOT_LOGOS_H
#include <genesis.h>
extern volatile u16 boot_stage,boot_tick;
extern volatile u8 boot_done;
void boot_logos(void);
#endif
