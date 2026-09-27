#include <genesis.h>
#include "high_score.h"
#include "frontend.h"
#include "boss_rush.h"
u32 high_score=20000;
HighScoreEntry high_scores[HIGH_SCORE_COUNT];
u8 high_score_pending=255,high_score_cursor;
static u32 saved_score,run_best,observed_score,table_generation;
static u8 save_slot,table_slot,table_dirty,run_recorded;
#define SAVE_MAGIC 0x42545331UL
#define TABLE_MAGIC 0x42544c32UL
#define SCORE_LIMIT 99999999UL
/* Keep the two v1.4 records intact. Two new 64-byte slots follow at 32/96. */
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
static u32 get32(const u8 *p){return ((u32)p[0]<<24)|((u32)p[1]<<16)|((u32)p[2]<<8)|p[3];}
static void put32(u8 *p,u32 value){p[0]=value>>24;p[1]=value>>16;p[2]=value>>8;p[3]=value;}
static u32 checksum(const u8 *p){
 u16 i;u32 h=2166136261UL;
 for(i=4;i<48;i++)h=(h^p[i])*16777619UL;
 return h;
}
static u8 table_read(u16 offset,u8 *data){
 u16 i;u32 previous=SCORE_LIMIT;
 for(i=0;i<52;i++)data[i]=SRAM_readByte(offset+i);
 if(get32(data)!=TABLE_MAGIC || get32(data+48)!=checksum(data))return 0;
 for(i=0;i<HIGH_SCORE_COUNT;i++){
  const u8 *p=data+8+i*8;u32 score=get32(p);u8 j;
  if(score>previous || p[7]>2)return 0;
  for(j=4;j<7;j++)if(p[j]!='-' && (p[j]<'A' || p[j]>'Z'))return 0;
  previous=score;
 }
 return 1;
}
__attribute__((noinline)) void high_score_init(void) {
 bool taken=begin_access();u32 a,b;u8 first[52],second[52],va,vb,*selected;u16 i;
 SRAM_enableRO();a=read_slot(0);b=read_slot(16);
 va=table_read(32,first);vb=table_read(96,second);end_access(taken);
 save_slot=b>a?1:0;saved_score=b>a?b:a;
 high_score=saved_score>20000?saved_score:20000;
 if(saved_score<20000)saved_score=20000;
 table_slot=vb && (!va || (s32)(get32(second+4)-get32(first+4))>0)?1:0;
 selected=table_slot?second:first;table_generation=va||vb?get32(selected+4):0;
 for(i=0;i<HIGH_SCORE_COUNT;i++){
  HighScoreEntry *entry=&high_scores[i];u8 j;
  entry->score=va||vb?get32(selected+8+i*8):i?0:high_score;
  for(j=0;j<3;j++)entry->initials[j]=va||vb?selected[12+i*8+j]:'-';
  entry->mode=va||vb?selected[15+i*8]:0;
 }
 table_dirty=!(va||vb);if(table_dirty)table_slot=1;
 if(high_scores[0].score>high_score)high_score=high_scores[0].score;
 high_score_pending=255;high_score_cursor=0;run_best=observed_score=0;run_recorded=0;
}
__attribute__((noinline)) static void table_save(void){
 u8 data[52],verify[52];u16 i,offset=32+(table_slot^1)*64;
 put32(data,TABLE_MAGIC);put32(data+4,table_generation+1);
 for(i=0;i<HIGH_SCORE_COUNT;i++){
  const HighScoreEntry *entry=&high_scores[i];u8 j;
  put32(data+8+i*8,entry->score);
  for(j=0;j<3;j++)data[12+i*8+j]=entry->initials[j];
  data[15+i*8]=entry->mode;
 }
 put32(data+48,checksum(data));
 SRAM_writeByte(offset,0);
 for(i=4;i<52;i++)SRAM_writeByte(offset+i,data[i]);
 for(i=1;i<4;i++)SRAM_writeByte(offset+i,data[i]);
 SRAM_writeByte(offset,data[0]);
 if(table_read(offset,verify) && !memcmp(data,verify,52)){
  table_generation++;table_slot^=1;table_dirty=0;
 }
}
void high_score_begin(void){run_best=observed_score=0;run_recorded=0;high_score_pending=255;}
void high_score_finish(void){
 u8 i,j;u32 score=game.score>run_best?game.score:run_best;
 if(run_recorded || frontend.debug_active || !score || score>SCORE_LIMIT)return;
 run_recorded=1;
 for(i=0;i<HIGH_SCORE_COUNT;i++)if(score>high_scores[i].score)break;
 if(i==HIGH_SCORE_COUNT)return;
 for(j=HIGH_SCORE_COUNT-1;j>i;j--)high_scores[j]=high_scores[j-1];
 high_scores[i].score=score;
 for(j=0;j<3;j++)high_scores[i].initials[j]='A';
 high_scores[i].mode=boss_rush.active || boss_rush.complete?2:frontend.mode;
 high_score_pending=i;high_score_cursor=0;table_dirty=1;
}
void high_score_letter(u8 up){
 if(high_score_pending<HIGH_SCORE_COUNT && high_score_cursor<3){
  char *c=&high_scores[high_score_pending].initials[high_score_cursor];
  *c=up?(*c=='Z'?'A':*c+1):(*c=='A'?'Z':*c-1);
 }
}
void high_score_confirm(void){high_score_pending=255;high_score_cursor=0;table_dirty=1;}
void high_score_save(void) {
 bool taken;u16 offset;u32 score;
 if(game.score!=observed_score){
  observed_score=game.score;
  if(observed_score>high_score)high_score=observed_score;
  if(game.mode!=TITLE && !frontend.debug_active && observed_score>run_best)run_best=observed_score;
 }
 score=high_score;
 if(!table_dirty && (score<=saved_score || score>SCORE_LIMIT))return;
 taken=begin_access();SRAM_enable();
 /* SRAM overlays upper ROM: interrupts, DMA and the Z80 are quiescent. */
 if(score>saved_score && score>20000 && score<=SCORE_LIMIT){
  offset=(save_slot^1)*16;SRAM_writeByte(offset,0);
  SRAM_writeLong(offset+4,score);SRAM_writeLong(offset+8,~score);
  SRAM_writeByte(offset+1,0x54);SRAM_writeByte(offset+2,0x53);SRAM_writeByte(offset+3,0x31);
  SRAM_writeByte(offset,0x42);
  if(read_slot(offset)==score){saved_score=score;save_slot^=1;}
 }
 if(table_dirty)table_save();
 end_access(taken);
}
