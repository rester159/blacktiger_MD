#ifndef ACTOR_DISPATCH_H
#define ACTOR_DISPATCH_H
#include "animation.h"
enum {DRAW_FALLBACK,DRAW_PIECE,DRAW_BODY,DRAW_DRAGON,DRAW_WAVE};
enum {BEHAVIOR_NORMAL,BEHAVIOR_EDGE,BEHAVIOR_REINFORCEMENT,BEHAVIOR_FLAILER,BEHAVIOR_WAVEBOSS,BEHAVIOR_ERUPTION,BEHAVIOR_TELEPORTER,BEHAVIOR_HUNTER,BEHAVIOR_CRAWLER,BEHAVIOR_STATUE,BEHAVIOR_BOULDER,BEHAVIOR_STONE,BEHAVIOR_ZOMBIE,BEHAVIOR_WISP,BEHAVIOR_EMERGE,BEHAVIOR_HAZARD};
typedef struct {const AnimFrame *(*frame)(u16 slot);u16 layout,behavior;} ActorDispatch;
extern const ActorDispatch actor_dispatch[];
/* 0: ordinary, 1: single actor boss, 2: layered boss. */
extern const u8 actor_boss_class[];
/* Native adapter: fallback, skeleton, common enemy, world object. */
extern const u8 actor_update_class[];
extern const u8 actor_weapon_enabled[];
typedef u8 (*ActorDamage)(u16 slot,u8 damage);
extern const ActorDamage actor_damage_routes[];
typedef u8 (*ActorVulnerable)(u16 slot);
extern const ActorVulnerable actor_vulnerable[];
#endif
