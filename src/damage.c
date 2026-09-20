#include "armor_break.h"
#include "damage.h"
#include "player_death.h"
#include "assets.h"
u8 player_attack_damage(u8 tier) {return player_weapon_damage[tier<1?0:tier>5?4:tier-1];}
void player_hurt_from(u8 damage,s16 source_x) {
    Player *p = &game.p;
    if (p->invincible || game.boss_dead || game.mode != PLAY) return;
    if (p->armor) {
        if (p->armor >= damage) {
            if(p->armor==damage)armor_break_start();else p->armor -= damage;
            p->invincible = 60;
            game.sound = SND_HIT;
            return;
        }
        damage -= p->armor;
        armor_break_start();
    }
    if (p->hp > damage) {
        p->hp -= damage;
        p->invincible = 60;
        game.sound = SND_HIT;
    } else {
        p->hp = 0;
        player_death_start(0,(u8)(PX(p->x)-game.cam_x)<(u8)(source_x-game.cam_x));
    }
}

void player_hurt(u8 damage) {player_hurt_from(damage,PX(game.p.x)+(game.p.face?1:-1));}
