#include <genesis.h>
#include "high_score.h"
#include "frontend.h"
#include "boss_rush.h"
u32 high_score=20000;
HighScoreEntry high_scores[HIGH_SCORE_COUNT];
u8 high_score_pending=255,high_score_cursor,high_score_mode;
static HighScoreEntry tables[3][HIGH_SCORE_COUNT];
static u32 saved_score,run_best,observed_score,table_generation;
static u8 save_slot,table_slot,table_dirty,run_recorded,settings_slot;
static u16 settings_generation;
static u8 saved_settings[14];
/* Share two bounded SRAM buffers between load/save paths. Keeping separate
   copies pushed SGDK's startup heap below the space needed for its default font. */
static u8 sram_workspace[2][132];
#define SAVE_MAGIC 0x42545331UL
#define TABLE_MAGIC 0x42544c32UL
#define TABLE3_MAGIC 0x42544c33UL
#define SETTINGS_MAGIC 0x42545343UL
#define SCORE_LIMIT 99999999UL
#define TABLE3_SIZE 132
static u32 read_slot(u16 offset) {
 u32 magic=SRAM_readLong(offset),score=SRAM_readLong(offset+4),inverse=SRAM_readLong(offset+8);
 return magic==SAVE_MAGIC && score<=SCORE_LIMIT && inverse==~score?score:0;
}
static bool begin_access(void) {
 SYS_disableInts();VDP_waitDMACompletion();return Z80_getAndRequestBus(TRUE);
}
static void end_access(bool taken) {SRAM_disable();if(!taken)Z80_releaseBus();SYS_enableInts();}
static u32 get32(const u8 *p){return ((u32)p[0]<<24)|((u32)p[1]<<16)|((u32)p[2]<<8)|p[3];}
static void put32(u8 *p,u32 value){p[0]=value>>24;p[1]=value>>16;p[2]=value>>8;p[3]=value;}
static u32 checksum(const u8 *p,u16 first,u16 last){u16 i;u32 h=2166136261UL;for(i=first;i<last;i++)h=(h^p[i])*16777619UL;return h;}
static u8 entry_valid(const u8 *p,u32 *previous){u32 score=get32(p);u8 j;if(score>*previous || p[7]>2)return 0;for(j=4;j<7;j++)if(p[j]!='-' && (p[j]<'A'||p[j]>'Z'))return 0;*previous=score;return 1;}
static u8 legacy_table_read(u16 offset,u8 *data){u16 i;u32 previous=SCORE_LIMIT;for(i=0;i<52;i++)data[i]=SRAM_readByte(offset+i);if(get32(data)!=TABLE_MAGIC||get32(data+48)!=checksum(data,4,48))return 0;for(i=0;i<5;i++)if(!entry_valid(data+8+i*8,&previous))return 0;return 1;}
static u8 table3_read(u16 offset,u8 *data){u16 i;u32 previous;
 for(i=0;i<TABLE3_SIZE;i++)data[i]=SRAM_readByte(offset+i);
 if(get32(data)!=TABLE3_MAGIC||get32(data+128)!=checksum(data,4,128))return 0;
 for(i=0;i<3;i++){u8 j;previous=SCORE_LIMIT;for(j=0;j<5;j++)if(!entry_valid(data+8+(i*5+j)*8,&previous))return 0;}
 return 1;
}
static void table_decode(const u8 *data){u8 m,i,j;for(m=0;m<3;m++)for(i=0;i<5;i++){const u8 *p=data+8+(m*5+i)*8;tables[m][i].score=get32(p);for(j=0;j<3;j++)tables[m][i].initials[j]=p[4+j];tables[m][i].mode=m;}}
static void table_encode(u8 *data){u8 m,i,j;put32(data,TABLE3_MAGIC);put32(data+4,table_generation+1);for(m=0;m<3;m++)for(i=0;i<5;i++){u8 *p=data+8+(m*5+i)*8;put32(p,tables[m][i].score);for(j=0;j<3;j++)p[4+j]=tables[m][i].initials[j];p[7]=m;}put32(data+128,checksum(data,4,128));}
void high_score_view(u8 mode){u8 i;high_score_mode=mode%3;for(i=0;i<5;i++)high_scores[i]=tables[high_score_mode][i];}
static u8 valid_settings(const u8 *d){return d[0]<4&&d[1]<8&&d[2]<8&&d[3]<2&&d[4]<2&&d[5]<2&&d[6]<99&&d[7]<4&&d[8]<8&&d[9]<2&&d[10]<2&&d[11]<2&&d[12]<2&&d[13]<99;}
static u8 settings_read(u16 offset,u8 *payload,u16 *generation){u8 d[24],i;for(i=0;i<24;i++)d[i]=SRAM_readByte(offset+i);if(get32(d)!=SETTINGS_MAGIC||get32(d+20)!=checksum(d,4,20)||!valid_settings(d+6))return 0;*generation=((u16)d[4]<<8)|d[5];memcpy(payload,d+6,14);return 1;}
static void settings_pack(u8 *d){u8 i,*p=(u8*)&settings[0];for(i=0;i<7;i++)d[i]=p[i];p=(u8*)&settings[1];for(i=0;i<7;i++)d[i+7]=p[i];}
static void settings_load(void){u8 a[14],b[14],i,va,vb;u16 ga=0,gb=0;va=settings_read(512,a,&ga);vb=settings_read(544,b,&gb);if(va||vb){settings_slot=vb&&(!va||(s16)(gb-ga)>0)?1:0;settings_generation=settings_slot?gb:ga;for(i=0;i<7;i++){u8 *p=(u8*)&settings[0];p[i]=(settings_slot?b:a)[i];p=(u8*)&settings[1];p[i]=(settings_slot?b:a)[i+7];}}settings_pack(saved_settings);}
__attribute__((noinline)) void high_score_init(void) {
 bool taken=begin_access();u32 a,b,legacy_best;u8 *old1=sram_workspace[0],*old2=sram_workspace[1],*new1=sram_workspace[0],*new2=sram_workspace[1],va,vb,oa,ob,*selected;u16 i;u32 max;
 SRAM_enableRO();a=read_slot(0);b=read_slot(16);va=table3_read(224,new1);vb=table3_read(368,new2);
 if(va||vb){table_slot=vb&&(!va||(s32)(get32(new2+4)-get32(new1+4))>0)?1:0;selected=table_slot?new2:new1;table_generation=get32(selected+4);table_decode(selected);table_dirty=0;}
 else {
  oa=legacy_table_read(32,old1);ob=legacy_table_read(96,old2);selected=ob&&(!oa||(s32)(get32(old2+4)-get32(old1+4))>0)?old2:old1;
  memset(tables,0,sizeof tables);for(i=0;i<15;i++){tables[i/5][i%5].initials[0]=tables[i/5][i%5].initials[1]=tables[i/5][i%5].initials[2]='-';tables[i/5][i%5].mode=i/5;}
  if(oa||ob){for(i=0;i<5;i++){const u8 *p=selected+8+i*8;u8 m=p[7];HighScoreEntry e;u8 j;e.score=get32(p);e.mode=m;for(j=0;j<3;j++)e.initials[j]=p[4+j];for(j=0;j<5;j++)if(e.score>tables[m][j].score)break;if(j<5){u8 k;for(k=4;k>j;k--)tables[m][k]=tables[m][k-1];tables[m][j]=e;}}}else tables[0][0]=(HighScoreEntry){20000,{'-','-','-'},0};
  table_generation=0;table_slot=1;table_dirty=1;
 }
 legacy_best=a>b?a:b;
 if(legacy_best&&!(va||vb)){u8 j;HighScoreEntry e;e.score=legacy_best;e.initials[0]=e.initials[1]=e.initials[2]='-';e.mode=0;for(j=0;j<5;j++)if(e.score>tables[0][j].score)break;if(j<5){u8 k;for(k=4;k>j;k--)tables[0][k]=tables[0][k-1];tables[0][j]=e;table_dirty=1;}}
 settings_load();end_access(taken);save_slot=b>a?1:0;saved_score=legacy_best;high_score=saved_score>20000?saved_score:20000;if(saved_score<20000)saved_score=20000;
 max=high_score;for(i=0;i<3;i++)if(tables[i][0].score>max)max=tables[i][0].score;high_score=max;
 high_score_mode=0;high_score_view(0);high_score_pending=255;high_score_cursor=0;run_best=observed_score=0;run_recorded=0;
}
static void table_save(void){u8 *data=sram_workspace[0],*verify=sram_workspace[1];u16 i,offset=table_slot?224:368;table_encode(data);SRAM_writeByte(offset,0);for(i=4;i<TABLE3_SIZE;i++)SRAM_writeByte(offset+i,data[i]);for(i=1;i<4;i++)SRAM_writeByte(offset+i,data[i]);SRAM_writeByte(offset,data[0]);if(table3_read(offset,verify)&&!memcmp(data,verify,TABLE3_SIZE)){table_generation++;table_slot^=1;table_dirty=0;}}
static u8 insert_score(u8 mode,u32 score){u8 i,j;for(i=0;i<5;i++)if(score>tables[mode][i].score)break;if(i==5)return 255;for(j=4;j>i;j--)tables[mode][j]=tables[mode][j-1];tables[mode][i].score=score;tables[mode][i].initials[0]=tables[mode][i].initials[1]=tables[mode][i].initials[2]='A';tables[mode][i].mode=mode;return i;}
void high_score_begin(void){run_best=observed_score=0;run_recorded=0;high_score_pending=255;}
void high_score_finish(void){u32 score=game.score>run_best?game.score:run_best;u8 mode=boss_rush.active||boss_rush.complete?2:frontend.mode?1:0;if(run_recorded||frontend.debug_active||!score||score>SCORE_LIMIT)return;run_recorded=1;high_score_pending=insert_score(mode,score);if(high_score_pending==255)return;high_score_view(mode);high_score_cursor=0;table_dirty=1;}
void high_score_letter(u8 up){if(high_score_pending<5&&high_score_cursor<3){char *c=&high_scores[high_score_pending].initials[high_score_cursor];*c=up?(*c=='Z'?'A':*c+1):(*c=='A'?'Z':*c-1);tables[high_score_mode][high_score_pending]=high_scores[high_score_pending];}}
void high_score_confirm(void){high_score_pending=255;high_score_cursor=0;table_dirty=1;}
static u8 settings_dirty(void){u8 current[14];settings_pack(current);return memcmp(saved_settings,current,14)!=0;}
static void settings_save(void){u8 d[24],payload[14],verify[14],i;u16 offset=settings_slot?512:544,gen=settings_generation+1,check;settings_pack(payload);put32(d,SETTINGS_MAGIC);d[4]=gen>>8;d[5]=gen;memcpy(d+6,payload,14);put32(d+20,checksum(d,4,20));SRAM_writeByte(offset,0);for(i=4;i<24;i++)SRAM_writeByte(offset+i,d[i]);for(i=1;i<4;i++)SRAM_writeByte(offset+i,d[i]);SRAM_writeByte(offset,d[0]);if(settings_read(offset,verify,&check)&&check==gen&&!memcmp(payload,verify,14)){memcpy(saved_settings,payload,14);settings_generation=gen;settings_slot^=1;}}
void high_score_save(void){bool taken;u16 offset;u32 score;u8 save_settings=settings_dirty();if(game.score!=observed_score){observed_score=game.score;if(observed_score>high_score)high_score=observed_score;if(game.mode!=TITLE&&!frontend.debug_active&&observed_score>run_best)run_best=observed_score;}score=high_score;if(!table_dirty&&(score<=saved_score||score>SCORE_LIMIT)&&!save_settings)return;taken=begin_access();SRAM_enable();if(score>saved_score&&score>20000&&score<=SCORE_LIMIT){offset=(save_slot^1)*16;SRAM_writeByte(offset,0);SRAM_writeLong(offset+4,score);SRAM_writeLong(offset+8,~score);SRAM_writeByte(offset+1,0x54);SRAM_writeByte(offset+2,0x53);SRAM_writeByte(offset+3,0x31);SRAM_writeByte(offset,0x42);if(read_slot(offset)==score){saved_score=score;save_slot^=1;}}if(table_dirty)table_save();if(save_settings)settings_save();end_access(taken);}
