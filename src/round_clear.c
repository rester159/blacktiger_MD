#include "round_clear.h"
#include "round_clear_data.inc"
RoundClear round_clear;
void round_clear_reset(void){round_clear=(RoundClear){0};}
u16 round_clear_reward(u8 round){return clear_coins[round];}
void round_clear_start(void){
 RoundClear *s=&round_clear;s->active=1;s->phase=1;s->profile=(game.p.weapon-1)*2+(game.p.armor!=0);
 s->x=PX(game.p.x)-game.cam_x;s->y=PX(game.p.y)-game.cam_y;s->original_armor=game.p.armor;
 s->index=s->remaining=0;if(!game.p.armor)game.p.armor=2;
}
u8 round_clear_step(void){
 RoundClear *s=&round_clear;const ClearClip *c=&clear_clips[s->profile];
 if(s->phase==2){if(game.mode_timer && --game.mode_timer)return 0;return 1;}
 if(s->remaining && --s->remaining)return 0;
 if(s->index==(game.round==7?c->ending_count:c->count)){
  if(game.round==7)return 1;
  game.coins+=clear_coins[game.round];game.mode_timer=240;s->phase=2;return 0;
 }
 s->remaining=c->frames[s->index++].ticks;return 0;
}
const ClearFrame *round_clear_frame(void){return round_clear.phase==1 && round_clear.index?&clear_clips[round_clear.profile].frames[round_clear.index-1]:0;}
