#include "progress.h"
#include "emerge.h"
#include "assets.h"
#include "hazard.h"
#include "loot.h"
typedef struct { AnimState animation; u8 phase, vulnerable, pending; } EmergeState;
static EmergeState emerging[MAX_ACTORS];
static u8 emerge_delay[160], emerge_seen[160], emerge_contact;
static const EmergeProfile *profile(u16 slot) {
    return &emerge_profiles[emerge_kinds[game.actors[slot].def] - 1];
}
void emerge_reset(void) {
    u16 i;
    for (i=0;i<160;i++) emerge_delay[i]=emerge_seen[i]=0;
    emerge_contact=0;
}
u8 emerge_spawn_ready(u16 row) {
    const Spawn *sp=&rounds[game.round].spawns[row];
    u8 target;
    if (!emerge_kinds[sp->def]) return 1;
    target=emerge_seen[row]?30:3;
    if (!emerge_seen[row] && (u8)(PX(game.p.x)+64-sp->x)>=128) return 0;
    if (emerge_delay[row]==target) return 1;
    emerge_delay[row]++;
    return 0;
}
void emerge_spawn(u16 slot) {
    Actor *a=&game.actors[slot];EmergeState *s=&emerging[slot];
    animation_reset(&s->animation);s->phase=s->vulnerable=s->pending=0;
    a->hp=profile(slot)->health;a->state=0;a->vx=a->vy=0;
    emerge_seen[a->source]=1;emerge_delay[a->source]=0;
}
u8 emerge_vulnerable(u16 slot) {return emerging[slot].vulnerable && !game.actors[slot].state;}
u8 emerge_hit(u16 slot,u8 damage) {
    Actor *a=&game.actors[slot];EmergeState *s=&emerging[slot];
    if (!emerge_kinds[a->def]) return 0;
    if (a->active && !a->state) {
        if (a->hp>damage) a->hp-=damage;
        else {a->state=1;s->pending=1;s->vulnerable=0;progress_score(profile(slot)->score);}
    }
    return 1;
}
u8 emerge_step(u16 slot) {
    Actor *a=&game.actors[slot];EmergeState *s=&emerging[slot];const EmergeProfile *p=profile(slot);
    if (s->pending) {
        s->pending=0;s->phase=5;animation_reset(&s->animation);
        game.spawned[a->source]=2;game.kills++;game.sound=SND_KILL;
        loot_spawn(drop_categories[a->def],loot_random>>8,PX(a->x),PX(a->y));
    }
    if (!animation_tick(&s->animation,p->clips[s->phase])) {
        switch(s->phase) {
        case 0:s->vulnerable=1;s->phase=1;break;
        case 1:s->phase=emerge_contact?4:2;break;
        case 2:case 4:s->vulnerable=0;emerge_contact=0;s->phase=3;break;
        default:
            a->active=0;
            if (!a->state) game.spawned[a->source]=0;
            return 0;
        }
        animation_reset(&s->animation);animation_tick(&s->animation,p->clips[s->phase]);
    }
    if (s->vulnerable && (game.frame & 1) &&
        player_contact(PX(a->x)+8,PX(a->y)+8,p->width,p->height)) {
        emerge_contact=1;
        return 1;
    }
    return 0;
}
const AnimFrame *emerge_frame(u16 slot) {
    EmergeState *s=&emerging[slot];
    return s->animation.remaining?animation_current(&s->animation,profile(slot)->clips[s->phase]):0;
}
