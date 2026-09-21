#include "frontend.h"
Frontend frontend;
GameSettings settings[2];
void frontend_init(void){u8 i;frontend=(Frontend){0};for(i=0;i<2;i++)settings[i]=(GameSettings){1,4,3,1,1,1,3};}
u8 frontend_lives(void){static const u8 lives[]={2,3,5,7};return lives[settings[frontend.mode].lives];}
void frontend_coin(u16 pressed){
 static const u8 needed[]={4,3,2,1,1,1,1,1},awarded[]={1,1,1,1,2,3,4,5};
 if(frontend.message)frontend.message--;
 if(frontend.mode==0 && (pressed&IN_COIN)){
  if(++frontend.coin_meter>=needed[settings[0].coinage]){
   u16 n=frontend.credits+awarded[settings[0].coinage];frontend.credits=n>99?99:n;frontend.arcade_credits=frontend.credits;frontend.coin_meter=0;game_sound(6);
  }
  frontend.revision++;
 }
}
u8 frontend_continue(void){return settings[frontend.mode].continues && frontend.credits!=0;}
void frontend_spend(void){if(frontend.credits)frontend.credits--;if(!frontend.mode)frontend.arcade_credits=frontend.credits;}
void frontend_return(void){frontend.page=1;frontend.selected=0;frontend.message=0;frontend.revision++;}
static u8 cycle(u8 value,u8 count,u8 down){return down?(value?value-1:count-1):(value+1==count?0:value+1);}
u8 frontend_step(u16 pressed){
 u8 home=frontend.mode,back=home?7:6;
 if(!pressed)return 0;
 frontend.revision++;
 if(frontend.page==0){
  if(pressed&(IN_UP|IN_DOWN))frontend.selected^=1;
  if(pressed&(IN_START|IN_ATTACK)){frontend.mode=frontend.selected;frontend.credits=frontend.mode?settings[1].credits:frontend.arcade_credits;frontend.page=1;frontend.selected=0;frontend.coin_meter=0;}
  return 0;
 }
 if(frontend.page==1){
  if(pressed&IN_JUMP){frontend.page=0;frontend.selected=frontend.mode;return 0;}
  if(pressed&IN_UP)frontend.selected=cycle(frontend.selected,home?3:2,1);
  if(pressed&IN_DOWN)frontend.selected=cycle(frontend.selected,home?3:2,0);
  if(pressed&(IN_START|IN_ATTACK)){
   if(frontend.selected==(home?2:1)){frontend.page=2;frontend.option=0;return 0;}
   if(!(pressed&IN_START))return 0;
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
  }
 }
 return 0;
}
