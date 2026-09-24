#include "eruption.h"
#include "assets.h"
typedef struct {AnimState animation;u8 segment,contact;} EruptionState;
static EruptionState eruptions[MAX_ACTORS];
static u8 eruption_delay[160];
void eruption_reset(void){u16 i;for(i=0;i<160;i++)eruption_delay[i]=0;}
u8 eruption_prepare(u16 row,s16 x,s16 y){
 s16 sx=x-game.cam_x,sy=y-game.cam_y;
 if((u16)sx>=256 || (u16)sy>=256)return 0;
 if((u8)(PX(game.p.x)-game.cam_x+64-sx)>=128 || (u8)(PX(game.p.y)-game.cam_y+10-sy)>=20)return 0;
 if(++eruption_delay[row]!=20)return 0;
 eruption_delay[row]=0;return 1;
}
static const AnimClip *clip(u16 slot){return eruption_clips[(eruption_kinds[game.actors[slot].def]-1)*3+eruptions[slot].segment];}
void eruption_spawn(u16 slot){EruptionState *s=&eruptions[slot];animation_reset(&s->animation);s->segment=s->contact=0;game.actors[slot].state=0;}
u8 eruption_contact(u16 slot){return eruptions[slot].contact;}
void eruption_step(u16 slot){
 EruptionState *s=&eruptions[slot];Actor *a=&game.actors[slot];
 for(;;){
  if(animation_step(&s->animation,clip(slot)))return;
  if(s->segment==2){a->active=0;game.spawned[a->source]^=1;return;}
  s->contact=s->segment==0;if(s->contact)game.sound=SND_ATTACK;
  s->segment++;animation_reset(&s->animation);
 }
}
const AnimFrame *eruption_frame(u16 slot){EruptionState *s=&eruptions[slot];return s->animation.remaining?animation_current(&s->animation,clip(slot)):0;}
