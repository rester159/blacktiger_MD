#include <genesis.h>
#include "high_score.h"
u32 high_score=20000;
static u32 saved_score;
static u8 save_slot;
#define SAVE_MAGIC 0x42545331UL
#define SCORE_LIMIT 99999999UL
/* Two 16-byte records; commit the magic last, preserving the other slot. */
static u32 read_slot(u16 offset) {
 u32 magic=SRAM_readLong(offset),score=SRAM_readLong(offset+4),inverse=SRAM_readLong(offset+8);
 return magic==SAVE_MAGIC && score<=SCORE_LIMIT && inverse==~score?score:0;
}
static bool begin_access(void) {
 SYS_disableInts();VDP_waitDMACompletion();
 return Z80_getAndRequestBus(TRUE);
}
static void end_access(bool taken) {
 SRAM_disable();if(!taken)Z80_releaseBus();SYS_enableInts();
}
void high_score_init(void) {
 bool taken=begin_access();u32 a,b;
 SRAM_enableRO();a=read_slot(0);b=read_slot(16);end_access(taken);
 save_slot=b>a?1:0;saved_score=b>a?b:a;
 high_score=saved_score>20000?saved_score:20000;
}
void high_score_save(void) {
 bool taken;u16 offset;u32 score;
 if(game.score>high_score)high_score=game.score;
 score=high_score;
 if(score<=saved_score || score<=20000 || score>SCORE_LIMIT)return;
 taken=begin_access();offset=(save_slot^1)*16;
 /* SRAM overlays upper ROM: interrupts, DMA and the Z80 are quiescent. */
 SRAM_enable();SRAM_writeByte(offset,0);
 SRAM_writeLong(offset+4,score);SRAM_writeLong(offset+8,~score);
 SRAM_writeByte(offset+1,0x54);SRAM_writeByte(offset+2,0x53);SRAM_writeByte(offset+3,0x31);
 SRAM_writeByte(offset,0x42);
 if(read_slot(offset)==score){saved_score=score;save_slot^=1;}
 end_access(taken);
}
