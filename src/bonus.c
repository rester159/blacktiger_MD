#include "bonus.h"
#include "assets.h"
#include "hazard.h"
#include "player_motion.h"
u8 bonus_entered,bonus_consumed,bonus_rows[128];
u16 bonus_saved_x,bonus_saved_y;
u8 bonus_phases[4],bonus_clock;
void bonus_animation_reset(void){u8 i;bonus_clock=0;for(i=0;i<4;i++)bonus_phases[i]=0;}
void bonus_tick(void){
 u8 bank;
 if(++bonus_clock==26)bonus_clock=0;
 bank=bonus_clock%13;
 if(bank<4)bonus_phases[bank]=bonus_clock>=13;
}
void bonus_reset(u8 preserve) {
 const BonusRound *r=&bonus_rounds[game.round];u16 i,shift=rounds[game.round].width==2048?7:6;
 bonus_animation_reset();bonus_entered=0;if(!preserve)bonus_consumed=0;
 for(i=0;i<128;i++)bonus_rows[i]=0;
 for(i=0;i<r->count;i++)bonus_rows[r->patches[i].cell>>shift]=1;
}
u8 bonus_gate(u8 jumping,u8 falling,u8 returning){return !(jumping|falling|returning);}
void bonus_destination(u8 round,u8 entered,u16 *x,u16 *y,u16 *sx,u16 *sy) {
 const BonusRound *r=&bonus_rounds[round];
 if(entered){*x=*sx;*y=*sy;}
 else {*sx=(*x&0xff00)|(u8)(*x+r->return_add);*sy=*y;*x=r->camera_x;*y=r->camera_y;}
}
u8 bonus_contact(void) {
 const BonusRound *r=&bonus_rounds[game.round];u8 i;
 if(!bonus_gate(player_motion.jumping,player_motion.falling,player_motion.camera_return))return 0;
 for(i=0;i<r->trigger_count;i++)if(!(bonus_consumed&(1<<i)) && player_contact(r->triggers[i].x,r->triggers[i].y,6,6)){
  bonus_consumed|=1<<i;return 1;
 }
 return 0;
}
static const BonusPatch *patch(u16 cell){
 const BonusRound *r=&bonus_rounds[game.round];u16 lo=0,hi=r->count;
 while(lo<hi){u16 mid=(lo+hi)>>1;if(r->patches[mid].cell<cell)lo=mid+1;else hi=mid;}
 return lo<r->count && r->patches[lo].cell==cell?r->patches+lo:0;
}
u16 bonus_word_state(u16 x,u16 y,u16 original,u8 entered,const u8 *phases){
 const BonusPatch *p;if(!bonus_rows[y>>1])return original;
 p=patch(((y>>1)<<(rounds[game.round].width==2048?7:6))+(x>>1));
 return p?p->words[entered*2+phases[p->bank]][((y&1)<<1)|(x&1)]:original;
}
u16 bonus_word(u16 x,u16 y,u16 original){return bonus_word_state(x,y,original,bonus_entered,bonus_phases);}
u8 bonus_collision(u16 cell,u8 original){
 const BonusPatch *p;if(!bonus_rows[cell>>(rounds[game.round].width==2048?7:6)])return original;
 p=patch(cell);return p?p->collision[bonus_entered*2+bonus_phases[p->bank]]:original;
}
