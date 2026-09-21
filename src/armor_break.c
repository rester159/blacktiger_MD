#include "armor_break.h"
#include "armor_break_data.inc"
ArmorFragment armor_fragments[4];
void armor_break_reset(void){u16 i;for(i=0;i<4;i++)armor_fragments[i]=(ArmorFragment){0};}
void armor_break_start(void){
    u16 i;if(!game.p.armor)return;
    game_sound(0x17);game.p.armor=0;
    for(i=0;i<4;i++)armor_fragments[i]=(ArmorFragment){.x=PX(game.p.x)+8,.y=PX(game.p.y)+8,.active=1};
}
void armor_break_step(void){
    u16 i;for(i=0;i<4;i++){
        ArmorFragment *f=&armor_fragments[i];if(!f->active)continue;
        animation_tick(&f->anim,&armor_clips[i]);
        f->x+=f->anim.vx;
        if(!small_actor_axis_active(f->x-game.cam_x,0)){f->active=0;continue;}
        f->y+=f->anim.vy;
        if(!small_actor_axis_active(f->y-game.cam_y,1))f->active=0;
    }
}
const AnimFrame *armor_break_frame(u16 i){
    return armor_fragments[i].active && armor_fragments[i].anim.remaining?animation_current(&armor_fragments[i].anim,&armor_clips[i]):0;
}
