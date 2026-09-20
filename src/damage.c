#include "damage.h"
#include "assets.h"
u8 player_attack_damage(u8 tier) {return player_weapon_damage[tier<1?0:tier>5?4:tier-1];}
void player_hurt(u8 damage) {
    Player *p = &game.p;
    if (p->invincible || game.mode != PLAY) return;
    if (p->armor) {
        if (p->armor >= damage) {
            p->armor -= damage;
            p->invincible = 60;
            game.sound = SND_HIT;
            return;
        }
        damage -= p->armor;
        p->armor = 0;
    }
    if (p->hp > damage) {
        p->hp -= damage;
        p->invincible = 60;
        game.sound = SND_HIT;
    } else {
        p->hp = 0;
        game.mode = DEAD;
        game.mode_timer = 120; /* Native death presentation remains provisional. */
        game.sound = SND_DIE;
    }
}
