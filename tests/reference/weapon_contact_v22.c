/* Pre-batching contact order, retained as a differential-test oracle. */
static void reference_contacts(void) {
    u16 i,j;u8 damage=player_attack.damage,pools;
    s16 y=PX(game.p.y)+(player_motion.jumping || player_motion.ladder || !(player_motion.selector&3)?6:14);
    if(player_attack.hit)return;
    if(!player_attack.count) {
        for(i=0;i<PLAYER_DAGGERS && player_daggers[i].active!=1;i++);
        if(i==PLAYER_DAGGERS)return;
    }
    /* Each source actor checks every extended link, then the nine daggers. */
    for(j=0;j<MAX_ACTORS;j++) {
        u8 chain_hit=0;
        if(!weapon_target(j))continue;
        for(i=0;i<player_attack.count;i++) {
            s16 x=PX(game.p.x)+(((player_attack.selector+1)&4)?-16-16*i:32+16*i);
            u8 contact=weapon_contact(j,x,y,0);
            if(contact) {
                if(contact==2)actor_hit(&game.actors[j],damage);
                player_attack_hit(&player_attack);chain_hit=1;break;
            }
        }
        for(i=0;i<PLAYER_DAGGERS;i++) {
            PlayerDagger *p=&player_daggers[i];u8 contact;
            if(p->active!=1)continue;
            contact=weapon_contact(j,p->x,p->y,1);
            if(contact) {
                if(contact==2)actor_hit(&game.actors[j],damage>1?damage>>1:1);
                player_dagger_hit(i,contact==1 || actor_dagger_effect[game.actors[j].def]);
            }
        }
        if(chain_hit)return;
    }
    pools=weapon_pools();
    if(!pools)return;
    for(i=0;i<player_attack.count;i++) {
        s16 x=PX(game.p.x)+(((player_attack.selector+1)&4)?-16-16*i:32+16*i);
        if(weapon_projectile(x,y,damage,0,pools)){player_attack_hit(&player_attack);return;}
    }
    for(i=0;i<PLAYER_DAGGERS;i++) {
        PlayerDagger *p=&player_daggers[i];
        if(p->active==1 && weapon_projectile(p->x,p->y,damage,1,pools))player_dagger_hit(i,0);
    }
}
