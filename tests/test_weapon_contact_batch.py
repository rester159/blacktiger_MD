#!/usr/bin/env python3
"""Compare optimized link/dagger scans to the pre-batching implementation.

Uses real constructor geometry and the oracle-tested scalar contact functions.
Damage callbacks are recorded stubs; linked-ROM tests exercise damage behavior.
"""
import ctypes as C, json, re, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def function(source,name):
    start=source.index(name+'(');start=source.rfind('\n',0,start)+1
    body=source.index('{',start);depth=1;end=body+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]
s=(ROOT/'src/game.c').read_text();data=(ROOT/'src/data.c').read_text();hazard=(ROOT/'src/hazard.c').read_text()
code='''#include <string.h>
#include "assets.h"
#include "player_motion.h"
#include "player_dagger.h"
#include "hazard.h"
#include "actor_dispatch.h"
Game game;PlayerMotion player_motion;PlayerAttack player_attack;
PlayerDagger player_daggers[PLAYER_DAGGERS];
static u32 result;static u32 rng=712;
static u32 random_word(void){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
static void record(u32 v){result=result*33+v;}
static void actor_hit(Actor *a,u8 damage){record(1000+(a-game.actors)*16+damage);a->hp=0;a->active=0;}
void player_attack_hit(PlayerAttack *p){record(2000);p->hit=1;}
void player_dagger_hit(u16 slot,u8 effect){record(3000+slot*2+!!effect);player_daggers[slot].active=2;}
static u8 weapon_target(u16 j){return game.actors[j].active && actor_weapon_enabled[game.actors[j].def];}
static u8 weapon_pools(void){return 0;}
static u8 weapon_projectile(s16 x,s16 y,u8 damage,u8 dagger,u8 pools){return 0;}
u8 dragon_weapon_contact(u16 j,s16 x,s16 y,u8 dagger){return 0;}
u8 waveboss_weapon_contact(u16 j,s16 x,s16 y,u8 dagger){return 0;}
'''
for name in ['actor_contact_pool','actor_contact_half_width','actor_contact_half_height','actor_dagger_effect','dragon_kinds','waveboss_kinds']:
    code+=re.search(r'const u8 '+name+r'\[\]=\{[^;]+;',data)[0]+'\n'
code+=re.search(r'const u8 actor_weapon_enabled\[\]=\{[^;]+;',(ROOT/'src/actor_dispatch.c').read_text())[0]+'\n'
code+='const u8 dagger_width=4,dagger_height=2;\n'
for name in ('actor_dagger_contact','actor_chain_contact'):code+=function(hazard,name)+'\n'
code+=function(s,'weapon_contact')+'\n'+(ROOT/'tests/reference/weapon_contact_v22.c').read_text()+'\n'+function(s,'player_weapons_contact')
code+='''
int compare(unsigned seed){
 Game initial;PlayerAttack attack;PlayerDagger daggers[PLAYER_DAGGERS];u32 expected;unsigned i;
 rng=seed+1;memset(&game,0,sizeof game);memset(&player_attack,0,sizeof player_attack);memset(&player_motion,0,sizeof player_motion);
 game.frame=random_word()&1;game.cam_x=(s16)(random_word()%4608-512);game.cam_y=random_word()%1800;
 game.p.x=((s16)game.cam_x+128)*256;game.p.y=(game.cam_y+144)*256;
 player_attack.count=random_word()%5;player_attack.damage=1+random_word()%8;player_attack.selector=(random_word()&1)?0:4;
 player_motion.selector=random_word()%8;player_motion.jumping=random_word()&1;
 for(i=0;i<MAX_ACTORS;i++){
  Actor *a=&game.actors[i];a->active=1;a->hp=5;a->def=random_word()%66;
  a->x=((s16)game.cam_x+(s16)(random_word()%400)-64)*256+(random_word()&255);
  a->y=(game.cam_y+(s16)(random_word()%340)-48)*256+(random_word()&255);
 }
 for(i=0;i<PLAYER_DAGGERS;i++){
  player_daggers[i]=(PlayerDagger){0};player_daggers[i].active=random_word()%3;
  player_daggers[i].x=(s16)game.cam_x+(s16)(random_word()%400)-64;
  player_daggers[i].y=game.cam_y+(s16)(random_word()%340)-48;
 }
 initial=game;attack=player_attack;memcpy(daggers,player_daggers,sizeof daggers);
 result=0;reference_contacts();expected=result;
 game=initial;player_attack=attack;memcpy(player_daggers,daggers,sizeof daggers);
 result=0;player_weapons_contact();return result==expected;
}
'''
with tempfile.TemporaryDirectory() as directory:
    tmp=Path(directory);(tmp/'genesis.h').write_text('');(tmp/'batch.c').write_text(code)
    subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(tmp/'batch.c'),'-o',str(tmp/'batch.dylib')],check=True)
    lib=C.CDLL(str(tmp/'batch.dylib'));lib.compare.argtypes=[C.c_uint]
    for seed in range(50000):assert lib.compare(seed),(seed,'contact order changed')
report=dict(passed=True,randomized_encounters=50000,actor_definitions=66,scope=__doc__)
(ROOT/'reports/weapon-contact-batch-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
