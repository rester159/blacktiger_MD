#include "game_over.h"
#include "music.h"
GameOver game_over;
void game_over_reset(void){game_over=(GameOver){0};}
void game_over_start(void){game_over=(GameOver){420,1,9};}
u8 game_over_step(u16 input){
 if(game_over.phase==1){
  if(--game_over.remaining)return 0;
  game_over.phase=2;game_over.remaining=750;music_request=0x34;return 0;
 }
 /* Original input polling follows each three-update scheduler wait.
    Console continues are free; no coin-input or credit bookkeeping is needed. */
 if(game_over.remaining%3==0 && (input&IN_START))return 1;
 if(!--game_over.remaining)return 2;
 game_over.digit=(game_over.remaining-1)/75;
 return 0;
}
