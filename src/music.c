#include "music.h"
typedef struct {const u8 *data;u32 length,loop_offset;u16 loop_tick,end_tick;} MusicTrack;
#include "music_data.inc"
u8 music_active,music_round,music_command,music_request;
u16 music_tick;
u32 music_writes;
static u32 position,fraction;
static void emit(u8 part,u8 reg,u8 value){music_write(part,reg,value);music_writes++;}
static void apply(void){
 const MusicTrack *t=&music_tracks[music_command-0x20];
 while(position<t->length){
  const u8 *p=t->data+position;u16 at=((u16)p[0]<<8)|p[1];u8 n;
  if(at>music_tick)return;
  n=p[2];position+=3;
  while(n--){p=t->data+position;emit(p[0],p[1],p[2]);position+=3;}
 }
}
void music_stop(void){u8 i;for(i=0;i<6;i++)emit(0,0x28,i<3?i:i+1);music_active=0;}
void music_start_command(u8 command){
 u8 p,ch;
 if(command<0x20 || command>0x39 || command==0x38)return;
 music_stop();music_command=command;
 if(command>=0x21 && command<=0x28)music_round=command-0x21;
 music_tick=0;position=fraction=0;music_active=1;
 for(p=0;p<2;p++)for(ch=0;ch<3;ch++)emit(p,0xb4+ch,0xc0);
 apply();
}
void music_start(u8 round){music_start_command(0x21+(round&7));}
void music_advance(u16 video_frames,u8 pal){
 const MusicTrack *t;u32 denominator=pal?61461:1791;
 if(!music_active)return;t=&music_tracks[music_command-0x20];
 while(video_frames--){
  /* Original timer: 3,579,545 / (72 * 199) updates/sec.
     NTSC display clock: (15 * 3,579,545) / (3420 * 262).
     PAL ratio approximates 53,203,424 / (3420 * 313), error < 1e-9. */
  fraction+=pal?308939:7467;
  while(fraction>=denominator){
   fraction-=denominator;
   if(++music_tick==t->end_tick){
    if(t->loop_tick==65535){apply();music_stop();return;}
    music_tick=t->loop_tick;position=t->loop_offset;
   }
   /* Most 250 Hz music ticks contain no writes. Avoid the FM stream
      writer's register-save prologue until its next event is actually due. */
   if(position<t->length) {
    const u8 *next=t->data+position;
    if((((u16)next[0]<<8)|next[1])<=music_tick)apply();
   }
  }
 }
}
