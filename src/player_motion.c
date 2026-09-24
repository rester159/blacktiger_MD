#include "player_motion.h"
/* Bank 7: 80C3 input, 8625 walk/climb, 8800 jump, 8F8D fall, 8126
 * integration. No source instructions or addresses are executed at runtime. */
u8 player_motion_sounds[4],player_motion_sound_count,player_motion_frame;
u8 player_motion_jump_assist;
static void cue(u8 command) {
    if(player_motion_sound_count<4)player_motion_sounds[player_motion_sound_count++]=command;
}
static u8 probe(const PlayerMotion *p, s16 x, s16 y) {
    return terrain((s16)(p->scroll_x+p->screen_x+x),
                   (s16)(p->scroll_y+p->screen_y+y));
}
static u8 facing(u8 selector) { return selector&3 ? (selector&2)<<1 : selector; }
static void gravity(PlayerMotion *p) {
    u16 velocity=(u16)((u8)p->vy*256+p->fraction+64);
    if ((velocity>>8)==5) velocity=1280;
    p->vy=(s8)(velocity>>8);p->fraction=(u8)velocity;
}
static void detach(PlayerMotion *p) {
    p->ladder=0;p->scroll_y-=(p->scroll_y+p->screen_y)&15;
}
static void attach(PlayerMotion *p) {
    cue(0x1e);p->ladder=1;p->scroll_x+=8-((p->scroll_x+p->screen_x)&15);
}
static void start_fall(PlayerMotion *p) {
    cue(0x3b);p->vx=p->vy=p->fraction=0;p->falling=1;
}
static void obstruction(PlayerMotion *p) {
    start_fall(p);p->below_origin=p->ladder=p->direction=0;
}
static void screen_floor(PlayerMotion *p) {
    p->screen_motion=0;p->below_origin=1;
    p->screen_y=(p->screen_y&0xff00)|144;
}
static void fall(PlayerMotion *p) {
    u8 ground;
    if (p->ladder && probe(p,16,16)==1) {
        p->vx=p->vy=p->falling=0;p->pose=12;cue(0x1f);return;
    }
    if (p->idle) {p->selector=p->previous;p->frame=0;}
    else {
        u8 b=p->selector;
        if (b==5 || (b&2)) b=p->previous;
        p->selector=p->previous=(b+1)&4;
    }
    if (p->jumping) {
        if (p->screen_y>p->jump_origin) screen_floor(p);
        ground=probe(p,p->direction&1?12:20,32)>=2;
    } else ground=probe(p,20,32)>=2 || probe(p,12,32)>=2;
    if (!ground) {gravity(p);return;}
    if (p->jumping) {
        if (p->below_origin) p->screen_y=(p->screen_y&0xff00)|144;
        else p->camera_return=1;
    }
    p->vy=p->fraction=p->falling=p->jump_request=p->jumping=0;
    p->frame=p->redirected=p->below_origin=0;cue(0x1f);cue(0x1c);detach(p);
}
static void walk(PlayerMotion *p) {
    static const s8 velocity[6][2]={{2,0},{0,0},{0,2},{0,0},{-2,0},{0,-2}};
    p->pose=0;
    if (p->idle) {
        p->selector=facing(p->previous);
        p->frame=p->vx=p->vy=p->direction=0;
    } else {
        if (++p->subtick==3) {p->subtick=0;++p->frame;}
        p->vx=velocity[p->selector][0];p->vy=velocity[p->selector][1];
        if (!(p->selector&3)) p->previous=p->selector;
    }
    switch(p->selector) {
    case 0:case 4:
        p->previous=p->selector;p->low=0;
        if (p->ladder) {p->pose=12;p->vx=0;return;}
        if (probe(p,p->selector==0?24:8,16)>=2) {p->vx=0;return;}
        if (probe(p,12,32)<2 && probe(p,20,32)<2) start_fall(p);
        return;
    case 1:case 3:
        p->previous=p->selector;
        if (p->ladder) p->pose=12;
        else {p->frame=0;p->low=1;}
        return;
    case 2:
        if (!p->ladder) {
            p->selector=(p->previous>>1)+(p->selector>>1);
            p->vy=0;p->low=1;return;
        }
        if (probe(p,16,16)==1) {
            if (probe(p,16,32)>=2) detach(p);
            else p->pose=12;
        } else if (probe(p,16,32)==1) p->pose=12;
        else {p->selector=p->previous;p->pose=18;start_fall(p);}
        return;
    case 5:
        p->low=0;
        if (p->ladder) {
            p->pose=12;
            if (probe(p,16,8)==1) return;
            p->frame=0;
        } else if (probe(p,16,8)==1) {attach(p);p->pose=12;return;}
        p->selector=facing(p->previous);p->vy=0;p->frame=0;return;
    }
}
static u8 jump(PlayerMotion *p,u8 input,u8 reversed,u8 attacking) {
    static const s8 horizontal[7]={0,2,-2,2,-2,2,-2};
    static const s16 vertical[7]={-1344,-1104,-1104,-1280,-1280,-912,-912};
    if (!attacking || !p->jumping) {
    if (p->idle) p->selector=p->previous;
    else {
        u8 b=p->selector;
        if (b==2 || b==5) b=p->previous;
        p->selector=p->previous=facing(b);
    }
    }
    if (!p->jumping) {
        if (p->ladder) {
            if (p->idle) goto cancel;
            if (!p->direction && (input&12)) {
                if ((input&12)!=8 || probe(p,16,8)==1) goto cancel;
                p->direction=0;p->selector=5;
            } else p->direction=((p->selector>>1)&3)?6:5;
        } else if (p->direction) {
            if (probe(p,p->direction&1?24:8,16)==2)
                p->direction=p->direction&1?5:6;
        } else p->selector=p->previous;
        if(!attacking)cue(0x1b);
        p->pose=6;p->jump_origin=p->camera_return?144:p->screen_y;
        p->screen_motion=p->jumping=1;
        p->vx=horizontal[p->direction];
        /* Home accessibility option: extra lift at takeoff; ordinary collision,
         * gravity and landing rules still govern the entire jump. */
        s16 launch=vertical[p->direction]-(player_motion_jump_assist?512:0);
        p->vy=(s8)((u16)launch>>8);
        p->fraction=(u8)launch;
    }
    if (p->vy<0) {
        if (probe(p,12,8)>=2 || probe(p,22,8)>=2 || (!attacking && (u8)p->screen_y<16)) {
            obstruction(p);return 0;
        }
        if (p->direction) {
            if (p->selector==2 || p->selector==5) p->selector=p->previous;
            if (((!attacking && p->ladder) || p->direction<5) && probe(p,p->direction&1?24:8,16)>=2) {
                obstruction(p);return 0;
            }
        } else if (!p->redirected && (u8)(p->jump_origin-p->screen_y)>=48) {
            p->redirected=1;
            if (!p->idle && (attacking ? input==1 || input==2 : (input&15)!=8 && (input&15)!=4)) {
                p->direction=attacking?input:(((input&2)!=0)^!!reversed?2:1);
                p->vx=p->direction==1?2:-2;
            }
        }
        if (!p->ladder && probe(p,16,16)==1) goto caught;
    } else {
        p->ladder=0;
        if (p->screen_y>=p->jump_origin) {
            if (attacking) {p->screen_motion=0;p->below_origin=1;}
            else screen_floor(p);
        }
        if (p->direction && probe(p,p->direction&1?24:8,16)>=2) {
            obstruction(p);return 0;
        }
        if (probe(p,16,16)==1) goto caught;
        if (probe(p,20,32)>=2 || probe(p,12,32)>=2) {
            p->pose=0;p->vx=p->vy=p->jumping=p->jump_request=0;
            p->frame=p->redirected=p->direction=0;
            if (!p->below_origin) p->camera_return=1;
            p->below_origin=0;detach(p);return 0;
        }
    }
    gravity(p);return 1;
caught:
    attach(p);p->pose=12;p->jumping=p->jump_request=p->redirected=0;
    p->frame=p->vx=p->vy=p->fraction=p->screen_motion=0;
    if (!p->below_origin) p->camera_return=1;
    p->below_origin=0;return 0;
cancel:
    p->jump_request=p->jumping=0;return 0;
}
/* Bank 7 8AEA: windup, one link per update, hold, then release. */
static void attack_step(PlayerMotion *p,PlayerAttack *a,u8 tier) {
    static const u8 reaches[5]={4,5,5,6,6};
    if (!a->active) {
        if (!p->jumping) {p->vx=0;if (!p->falling)p->vy=0;}
        if(tier>4)tier=4;
        a->reach=reaches[tier];a->damage=1<<tier;
        a->counter=a->links=0;
        if (p->idle) p->selector=p->previous=(p->previous+1)&4;
        else if (p->selector==2) {
            if (!(p->previous&3)) p->selector=(p->previous>>1)+1;
            else p->selector=p->previous;
        } else if (p->selector==5) p->selector=p->previous;
        else if (!(p->selector&3))p->previous=p->selector;
        a->selector=p->selector;a->active=1;cue(0x3a);
    }
    p->selector=a->selector;
    if (!a->count && a->counter<6) {
        p->pose=p->jumping?8:p->ladder?14:2;
    } else {
        if (!a->count)a->counter=0;
        p->pose=p->jumping?10:p->ladder?16:4;
        if (!a->holding) {
            if (a->counter==a->reach) {a->counter=0;a->holding=1;}
            else {if(a->counter)++a->links;a->count=a->counter+1;}
        }
        if (a->holding && a->counter>=13) {
            a->hit=a->active=a->request=a->holding=a->count=0;
            p->pose=p->jumping?6:p->ladder?12:0;return;
        }
    }
    ++a->counter;
    if (p->falling) fall(p);
}
void player_attack_hit(PlayerAttack *a) {a->holding=a->hit=1;a->counter=10;}
void player_control_step(PlayerMotion *p,PlayerAttack *attack,u8 input,u8 reversed,u8 tier) {
    static const u8 direction[2][16]={{0,1,2,0,0,0,0,0,0,3,4,0,0,0,0,0},
                                    {0,2,1,0,0,0,0,0,0,4,3,0,0,0,0,0}};
    static const u8 selector[2][16]={{0,0,4,0,2,1,3,0,5,0,4,0,0,0,0,0},
                                   {0,4,0,0,2,4,1,0,5,4,0,0,0,0,0,0}};
    u8 nibble=input&15;
    player_motion_sound_count=0;
    p->idle=!nibble;
    if (nibble) {
        if (!p->jumping) p->direction=direction[!!reversed][nibble];
        p->selector=selector[!!reversed][nibble];
    }
    p->jump_history=(p->jump_history<<1)|((input>>5)&1);
    if ((p->jump_history&7)==1) p->jump_request=1;
    if(attack) {
        attack->history=(attack->history<<1)|((input>>4)&1);
        if((attack->history&7)==1)attack->request=attack->launch=1;
    }
    if(attack && attack->request) {
        if(p->falling || !p->jump_request || jump(p,input,reversed,1)) attack_step(p,attack,tier);
    } else if (p->falling) fall(p);
    else if (p->jump_request) jump(p,input,reversed,0);
    else walk(p);
    if (!p->jumping && p->camera_return) {
        u8 y=(u8)p->screen_y;
        if (y<144) {
            u8 shift=144-y;if (shift>8) shift=8;
            p->scroll_y-=shift;p->screen_y+=shift;
        } else {p->camera_return=0;p->screen_y=(p->screen_y&0xff00)|144;p->screen_motion=0;}
    }
    p->scroll_x+=p->vx;
    if (p->screen_motion) p->screen_y+=p->vy;
    else {
        p->scroll_y+=p->vy;
        if((p->ladder&(((u8)p->vy>>1)|((u8)p->vy<<7))) && !(player_motion_frame&15))cue(0x1a);
    }
}

void player_motion_step(PlayerMotion *p,u8 input,u8 reversed) {
    player_control_step(p,0,input,reversed,0);
}
