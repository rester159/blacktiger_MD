"""Compile native frame-function routing once instead of scanning families per draw."""
from arcade_source import ROOT

def emit(definitions,skeleton):
 groups=[
 ('pair_frame','DRAW_PIECE',[(2,0xacac)]),
 ('edge_actor_frame','DRAW_BODY',[(4,0xa4d0)]),
 ('reinforcement_body_frame','DRAW_BODY',[(2,v) for v in (0x8344,0x9af6,0x8ef4)]),
 ('flailer_frame','DRAW_BODY',[(0,v) for v in (0xab33,0xab4a,0xb1c1,0xb1d8)]),
 ('dragon_frame','DRAW_DRAGON',[(3,v) for v in (0x8000,0x991d,0x9b24)]),
 ('waveboss_frame','DRAW_WAVE',[(1,v) for v in (0x98a3,0x98e8)]),
 ('eruption_frame','DRAW_BODY',[(1,v) for v in (0x8a5d,0x8a03,0x8b9b,0x8bf5)]),
 ('teleporter_frame','DRAW_BODY',[(1,v) for v in (0x92e6,0x8d33)]),
 ('hunter_frame','DRAW_BODY',[(1,v) for v in (0x9f83,0x9fc4)]),
 ('crawler_frame','DRAW_PIECE',[(3,v) for v in (0xaab3,0xb153,0xb7f3)]+[(7,0xa3b6)]),
 ('statue_frame','DRAW_BODY',[(0,0xb84f)]),
 ('boulder_frame','DRAW_BODY',[(4,0xb338)]),
 ('boss_frame','DRAW_BODY',[(4,v) for v in (0x9eb1,0x9f16,0x9a4c)]),
 ('zombie_frame','DRAW_BODY',[(0,v) for v in (0x8000,0x8389,0x89c6)]),
 ('wisp_frame','DRAW_BODY',[(2,0xa6f8)]),
 ('emerge_frame','DRAW_BODY',[(2,v) for v in (0x8000,0x81a2)]),
 ('sentry_frame','DRAW_BODY',[(2,0xb67f)]),
 ('skeleton_frame','DRAW_BODY',[(0,v) for v in skeleton['constructors']])]
 rows=[];vulnerability=[];boss_classes=[];update_classes=[];weapon_enabled=[];damage_routes=[]
 for d in definitions:
  function,layout='0','DRAW_FALLBACK'
  if d['kind']==5:function,layout='container_frame','DRAW_BODY'
  else:
   for name,style,keys in groups:
    if (d['bank'],d['address']) in keys:function,layout=name,style;break
   else:
    if d['kind']==9:function,layout='hidden_frame','DRAW_PIECE'
    elif d['npc_kind']:function,layout='npc_frame','DRAW_BODY'
  behavior={'edge_actor_frame':'EDGE','reinforcement_body_frame':'REINFORCEMENT','flailer_frame':'FLAILER','waveboss_frame':'WAVEBOSS','eruption_frame':'ERUPTION','teleporter_frame':'TELEPORTER','hunter_frame':'HUNTER','crawler_frame':'CRAWLER','statue_frame':'STATUE','boulder_frame':'BOULDER','boss_frame':'STONE','zombie_frame':'ZOMBIE','wisp_frame':'WISP','emerge_frame':'EMERGE'}.get(function,'NORMAL')
  if (d['bank'],d['address'])==(1,0xb2a9):behavior='HAZARD'
  boss_classes.append(2 if (d['bank'],d['address']) in ((4,0x9eb1),(4,0x9f16)) else int(function in ('dragon_frame','waveboss_frame') or (d['bank'],d['address'])==(1,0x9fc4)))
  update_classes.append(1 if function=='skeleton_frame' else 2 if function in ('wisp_frame','crawler_frame','zombie_frame') else 3 if d['kind'] in (5,6,9) else 0)
  rows.append('{'+function+','+layout+',BEHAVIOR_'+behavior+'}')
  check='0'
  if d['kind'] in (4,5,6,7) or function=='eruption_frame':check='actor_never_vulnerable'
  elif d['kind']==9:check='actor_hidden_vulnerable'
  elif function in ('waveboss_frame','flailer_frame','reinforcement_body_frame','edge_actor_frame','teleporter_frame','hunter_frame','crawler_frame','statue_frame','pair_frame','boss_frame','zombie_frame','emerge_frame'):
   check=function.removesuffix('_frame')+'_vulnerable'
  damage='0'
  if function=='wisp_frame':damage='actor_wisp_hit'
  elif function=='eruption_frame':damage='actor_ignore_hit'
  elif function not in ('0','hidden_frame','npc_frame','container_frame'):damage=function.removesuffix('_frame')+'_hit'
  damage_routes.append(damage)
  vulnerability.append(check)
  weapon_enabled.append(int(check!='actor_never_vulnerable'))
 (ROOT/'src/actor_dispatch.c').write_text('/* Generated native function routing; no arcade code is executed. */\n#include "actor_dispatch.h"\n#include "assets.h"\n#include "npc.h"\n#include "zombie.h"\n#include "sentry.h"\n#include "world.h"\nconst ActorDispatch actor_dispatch[]={\n'+',\n'.join(rows)+'\n};\nstatic u8 actor_never_vulnerable(u16 slot){(void)slot;return 0;}\nstatic u8 actor_hidden_vulnerable(u16 slot){return !game.actors[slot].state;}\nconst ActorVulnerable actor_vulnerable[]={\n'+',\n'.join(vulnerability)+'\n};\n')

 (ROOT/'src/actor_dispatch.c').open('a').write('const u8 actor_boss_class[]={'+','.join(map(str,boss_classes))+'};\n')

 (ROOT/'src/actor_dispatch.c').open('a').write('const u8 actor_update_class[]={'+','.join(map(str,update_classes))+'};\n')

 (ROOT/'src/actor_dispatch.c').open('a').write('const u8 actor_weapon_enabled[]={'+','.join(map(str,weapon_enabled))+'};\n')

 (ROOT/'src/actor_dispatch.c').open('a').write('static u8 actor_wisp_hit(u16 slot,u8 damage){(void)damage;return wisp_hit(slot);}\nstatic u8 actor_ignore_hit(u16 slot,u8 damage){(void)slot;(void)damage;return 0;}\nconst ActorDamage actor_damage_routes[]={'+','.join(damage_routes)+'};\n')
