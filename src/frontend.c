#include "frontend.h"
#include "music.h"
#include "high_score.h"
Frontend frontend;
GameSettings settings[2];
void frontend_init(void){u8 i;frontend=(Frontend){.debug_invincible=1,.debug_lives=1,.debug_time=1,.debug_framerate=1,.debug_zenny=1};for(i=0;i<2;i++)settings[i]=(GameSettings){1,4,3,1,1,1,3};}
u8 frontend_lives(void){static const u8 lives[]={2,3,5,7};return lives[settings[frontend.mode].lives];}
void frontend_coin(u16 pressed){
 static const u8 needed[]={4,3,2,1,1,1,1,1},awarded[]={1,1,1,1,2,3,4,5};
 if(frontend.message)frontend.message--;
 if(frontend.mode==0 && !(game.mode==TITLE && frontend.page==0) && (pressed&IN_START)){
  if(settings[0].sfx)music_request=0x20;
  if(++frontend.coin_meter>=needed[settings[0].coinage]){
   u16 n=frontend.credits+awarded[settings[0].coinage];frontend.credits=n>9?9:n;frontend.arcade_credits=frontend.credits;frontend.coin_meter=0;
  }
  frontend.revision++;
 }
}
u8 frontend_continue(void){return settings[frontend.mode].continues && frontend.credits!=0;}
void frontend_spend(void){if(frontend.credits)frontend.credits--;if(!frontend.mode)frontend.arcade_credits=frontend.credits;}
void frontend_return(void){high_score_finish();frontend.page=high_score_pending<5?6:1;frontend.selected=0;frontend.message=0;frontend.revision++;}
static u8 cycle(u8 value,u8 count,u8 down){return down?(value?value-1:count-1):(value+1==count?0:value+1);}
u8 frontend_step(u16 pressed){
 u8 home=frontend.mode,back=home?8:6;
 if(!home && frontend.page!=0)pressed&=~IN_START;
 if(!pressed)return 0;
 frontend.revision++;
 if(home && frontend.page==1 && !frontend.debug_unlocked){
  static const u16 code[]={IN_UP,IN_UP,IN_DOWN,IN_DOWN,IN_LEFT,IN_RIGHT,IN_LEFT,IN_RIGHT};
  if(pressed==code[frontend.debug_code])frontend.debug_code++;
  else frontend.debug_code=pressed==IN_UP?(frontend.debug_code==2?2:1):0;
  if(frontend.debug_code==8){
   frontend.debug_unlocked=1;frontend.debug_code=0;frontend.selected=3;
   game.sound=SND_COIN;return 0;
  }
 }else frontend.debug_code=0;
 if(frontend.page==5 || frontend.page==6){
  if(frontend.page==6){
   if(pressed&IN_UP)high_score_letter(1);
   if(pressed&IN_DOWN)high_score_letter(0);
   if((pressed&IN_JUMP) && high_score_cursor)high_score_cursor--;
   if(pressed&(IN_ATTACK|IN_START)){
    if(++high_score_cursor==3){high_score_confirm();frontend.page=home?5:1;}
   }
  }else {
   if(pressed&IN_LEFT)high_score_view(high_score_mode?high_score_mode-1:2);
   if(pressed&IN_RIGHT)high_score_view((high_score_mode+1)%3);
   if(pressed&(IN_JUMP|IN_ATTACK|IN_START)){frontend.page=0;frontend.selected=2;}
  }
  return 0;
 }
 if(frontend.page==0){
  if(pressed&IN_UP)frontend.selected=cycle(frontend.selected,3,1);
  if(pressed&IN_DOWN)frontend.selected=cycle(frontend.selected,3,0);
  if(frontend.selected==2 && (pressed&(IN_START|IN_ATTACK))){frontend.page=5;return 0;}
  if(pressed&(IN_START|IN_ATTACK)){frontend.mode=frontend.selected;frontend.credits=frontend.mode?settings[1].credits:frontend.arcade_credits;frontend.page=1;frontend.selected=0;frontend.coin_meter=0;}
  return 0;
 }
 if(frontend.page==4){
  if(pressed&IN_JUMP){frontend.page=1;frontend.selected=3;return 0;}
  /* Six rows in each column: two switches followed by four levels. */
  static const u8 items[12]={0,1,4,5,6,7,2,3,8,9,10,11};
  u8 slot=0;
  if(frontend.debug_option==12){
   if(pressed&IN_UP)frontend.debug_option=7;
   if(pressed&IN_DOWN)frontend.debug_option=0;
   if(pressed&IN_LEFT)frontend.debug_option=7;
   if(pressed&IN_RIGHT)frontend.debug_option=11;
   if(pressed&(IN_START|IN_ATTACK))frontend.debug_zenny^=1;
   return 0;
  }
  while(items[slot]!=frontend.debug_option)slot++;
  if(((pressed&IN_DOWN) && slot%6==5) || ((pressed&IN_UP) && slot%6==0)){
   frontend.debug_option=12;return 0;
  }
  if(pressed&IN_UP)slot=slot/6*6+(slot%6+5)%6;
  if(pressed&IN_DOWN)slot=slot/6*6+(slot%6+1)%6;
  if(pressed&(IN_LEFT|IN_RIGHT))slot=slot<6?slot+6:slot-6;
  frontend.debug_option=items[slot];
  if(pressed&(IN_START|IN_ATTACK)){
   switch(frontend.debug_option){
    case 0:frontend.debug_invincible^=1;break;
    case 1:frontend.debug_lives^=1;break;
    case 2:frontend.debug_time^=1;break;
    case 3:frontend.debug_framerate^=1;break;
    default:frontend.level=frontend.debug_option-4;
     frontend.credits=settings[1].credits;frontend_spend();return 3;
   }
  }
  return 0;
 }
 if(frontend.page==1){
  if(pressed&IN_JUMP){frontend.page=0;frontend.selected=frontend.mode;return 0;}
  if(!home){
   if(pressed&(IN_UP|IN_DOWN)){frontend.page=2;frontend.option=0;return 0;}
   if(pressed&IN_ATTACK){if(frontend.credits){frontend_spend();return 1;}frontend.message=120;}
   return 0;
  }
  if(home){
   if(pressed&IN_UP)frontend.selected=cycle(frontend.selected,frontend.debug_unlocked?4:3,1);
   if(pressed&IN_DOWN)frontend.selected=cycle(frontend.selected,frontend.debug_unlocked?4:3,0);
   if(pressed&(IN_LEFT|IN_RIGHT)){
    u8 next=frontend.selected^2;
    frontend.selected=next==3 && !frontend.debug_unlocked?2:next;
   }
  }else if(pressed&(IN_UP|IN_DOWN))frontend.selected^=1;
  if(pressed&(IN_START|IN_ATTACK)){
   if(frontend.selected==(home?2:1)){frontend.page=2;frontend.option=0;return 0;}
   if(home && frontend.debug_unlocked && frontend.selected==3){frontend.page=4;frontend.debug_option=0;return 0;}
   if(!(pressed&(home?IN_START:IN_ATTACK)))return 0;
   if(home)frontend.credits=settings[1].credits;
   if(!frontend.credits){frontend.message=120;return 0;}
   frontend_spend();return home && frontend.selected==1?2:1;
  }
  return 0;
 }
 if(pressed&IN_UP)frontend.option=cycle(frontend.option,back+1,1);
 if(pressed&IN_DOWN)frontend.option=cycle(frontend.option,back+1,0);
 if((pressed&IN_JUMP) || (frontend.option==back && (pressed&(IN_START|IN_ATTACK)))){frontend.page=1;return 0;}
 if(pressed&(IN_LEFT|IN_RIGHT|IN_ATTACK|IN_START)){
  GameSettings *s=&settings[home];u8 down=(pressed&IN_LEFT)!=0;
  switch(frontend.option){
   case 0:s->lives=cycle(s->lives,4,down);break;
   case 1:s->difficulty=cycle(s->difficulty,8,down);break;
   case 2:s->coinage=cycle(s->coinage,8,down);frontend.coin_meter=0;break;
   case 3:s->continues^=1;break;
   case 4:s->music^=1;break;
   case 5:s->sfx^=1;break;
   case 6:if(home)s->credits=1+cycle(s->credits-1,99,down);break;
   case 7:if(home)frontend.level7_jump_assist^=1;break;
  }
 }
 return 0;
}
