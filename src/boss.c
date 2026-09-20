#include "boss.h"
#include "assets.h"
void boss_spawn(u16 slot) {
 Actor *a=&game.actors[slot];u8 kind=layered_boss_kinds[a->def];
 if(kind)a->life=layered_boss_layers[kind-1];
}
u8 boss_break_layer(Actor *a) {
 if(!layered_boss_kinds[a->def])return 0;
 if(a->life>1){a->life--;a->hp=layered_boss_reset_health;game.sound=SND_HIT;return 1;}
 a->life=0;return 0;
}
