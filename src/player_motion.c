#include "player_motion.h"
/* Bank 7: 80C3 input, 8625 walk/climb, 8800 jump, 8F8D fall, 8126
 * integration. No source instructions or addresses are executed at runtime. */
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
    p->ladder=1;p->scroll_x+=8-((p->scroll_x+p->screen_x)&15);
}
static void start_fall(PlayerMotion *p) {
    p->vx=p->vy=p->fraction=0;p->falling=1;
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
        p->vx=p->vy=p->falling=0;p->pose=12;return;
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
    p->frame=p->redirected=p->below_origin=0;detach(p);
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
static void jump(PlayerMotion *p,u8 input,u8 reversed) {
    static const s8 horizontal[7]={0,2,-2,2,-2,2,-2};
    static const s16 vertical[7]={-1344,-1104,-1104,-1280,-1280,-912,-912};
    if (p->idle) p->selector=p->previous;
    else {
        u8 b=p->selector;
        if (b==2 || b==5) b=p->previous;
        p->selector=p->previous=facing(b);
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
        p->pose=6;p->jump_origin=p->camera_return?144:p->screen_y;
        p->screen_motion=p->jumping=1;
        p->vx=horizontal[p->direction];
        p->vy=(s8)((u16)vertical[p->direction]>>8);
        p->fraction=(u8)vertical[p->direction];
    }
    if (p->vy<0) {
        if (probe(p,12,8)>=2 || probe(p,22,8)>=2 || (u8)p->screen_y<16) {
            obstruction(p);return;
        }
        if (p->direction) {
            if (p->selector==2 || p->selector==5) p->selector=p->previous;
            if ((p->ladder || p->direction<5) && probe(p,p->direction&1?24:8,16)>=2) {
                obstruction(p);return;
            }
        } else if (!p->redirected && (u8)(p->jump_origin-p->screen_y)>=48) {
            p->redirected=1;
            if (!p->idle && (input&15)!=8 && (input&15)!=4) {
                p->direction=((input&2)!=0)^!!reversed?2:1;
                p->vx=p->direction==1?2:-2;
            }
        }
        if (!p->ladder && probe(p,16,16)==1) goto caught;
    } else {
        p->ladder=0;
        if (p->screen_y>=p->jump_origin) screen_floor(p);
        if (p->direction && probe(p,p->direction&1?24:8,16)>=2) {
            obstruction(p);return;
        }
        if (probe(p,16,16)==1) goto caught;
        if (probe(p,20,32)>=2 || probe(p,12,32)>=2) {
            p->pose=0;p->vx=p->vy=p->jumping=p->jump_request=0;
            p->frame=p->redirected=p->direction=0;
            if (!p->below_origin) p->camera_return=1;
            p->below_origin=0;detach(p);return;
        }
    }
    gravity(p);return;
caught:
    attach(p);p->pose=12;p->jumping=p->jump_request=p->redirected=0;
    p->frame=p->vx=p->vy=p->fraction=p->screen_motion=0;
    if (!p->below_origin) p->camera_return=1;
    p->below_origin=0;return;
cancel:
    p->jump_request=p->jumping=0;
}
void player_motion_step(PlayerMotion *p,u8 input,u8 reversed) {
    static const u8 direction[2][16]={{0,1,2,0,0,0,0,0,0,3,4,0,0,0,0,0},
                                    {0,2,1,0,0,0,0,0,0,4,3,0,0,0,0,0}};
    static const u8 selector[2][16]={{0,0,4,0,2,1,3,0,5,0,4,0,0,0,0,0},
                                   {0,4,0,0,2,4,1,0,5,4,0,0,0,0,0,0}};
    u8 nibble=input&15;
    p->idle=!nibble;
    if (nibble) {
        if (!p->jumping) p->direction=direction[!!reversed][nibble];
        p->selector=selector[!!reversed][nibble];
    }
    p->jump_history=(p->jump_history<<1)|((input>>5)&1);
    if ((p->jump_history&7)==1) p->jump_request=1;
    if (p->falling) fall(p);
    else if (p->jump_request) jump(p,input,reversed);
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
    else p->scroll_y+=p->vy;
}
