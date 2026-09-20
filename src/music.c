#include "music.h"
typedef struct {const u8 *data;u32 length,loop_offset;u16 loop_tick,end_tick;} MusicTrack;
#include "music_data.inc"
u8 music_active,music_round;
u16 music_tick;
u32 music_writes;
static u32 position,fraction;
static void emit(u8 part,u8 reg,u8 value){music_write(part,reg,value);music_writes++;}
static void apply(void){
 const MusicTrack *t=&music_tracks[music_round];
 while(position<t->length){
  const u8 *p=t->data+position;u16 at=((u16)p[0]<<8)|p[1];u8 n;
  if(at>music_tick)return;
  n=p[2];position+=3;
  while(n--){p=t->data+position;emit(p[0],p[1],p[2]);position+=3;}
 }
}
void music_stop(void){u8 i;for(i=0;i<6;i++)emit(0,0x28,i<3?i:i+1);music_active=0;}
void music_start(u8 round){
 u8 p,ch;music_stop();music_round=round&7;music_tick=0;position=fraction=0;music_active=1;
 for(p=0;p<2;p++)for(ch=0;ch<3;ch++)emit(p,0xb4+ch,0xc0);
 apply();
}
void music_advance(u16 video_frames,u8 pal){
 const MusicTrack *t;u32 denominator=pal?61461:1791;
 if(!music_active)return;t=&music_tracks[music_round];
 while(video_frames--){
  /* Original timer: 3,579,545 / (72 * 199) updates/sec.
     NTSC display clock: (15 * 3,579,545) / (3420 * 262).
     PAL ratio approximates 53,203,424 / (3420 * 313), error < 1e-9. */
  fraction+=pal?308939:7467;
  while(fraction>=denominator){
   fraction-=denominator;
   if(++music_tick==t->end_tick){music_tick=t->loop_tick;position=t->loop_offset;}
   apply();
  }
 }
}
