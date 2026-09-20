"""Development contract for the second recurring walker; not runtime Z80 code."""
import json
from arcade_source import Source,ROOT
from extract_animation import compile_clip
ROOTS=[0x869e,0x8738,0x86c0,0x87db,0x87b0,0x8848,0x8840,0x8850,0x8930,
       0x8813,0x8806,0x8830,0x8820,0x8838,0x8828,0x886a,0x8933,0x8966,
       0x8884,0x88da,0x8999,0x89b1,0x899c]
EVENTS={0x8418:'disable_contact',0x841f:'enable_contact',0x8430:'choose_walk_or_throw',
        0x851c:'walk_step',0x85e7:'fall_step',0x861f:'death_drop',0x84b6:'throw',
        0x8597:'jump_start',0x859b:'jump_step',0x8637:'projectile_hit'}
def extract(s):
 s.expect(0,0x83a6,'214e86013000edb0')
 s.expect(0,0x84c0,'217e86012000edb0')
 s.expect(0,0x8430,'dd7e21a720083a09e0e603ca8e84')
 s.expect(0,0x850e,'dd362101c33e84')
 s.expect(0,0x8597,'dd3607fc')
 s.expect(0,0x85af,'dd7e20d603dd7720da7385')
 actor=s.read(0,0x864e,48);weapon=s.read(0,0x867e,32)
 segments=[];indices={};pending=[]
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,ROOTS))
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,0,pc);event='retire';nxt=None
  if clip['terminal']=='event':
   event=EVENTS[clip['event']['address']]
   if event in ('disable_contact','enable_contact','walk_step'):nxt=intern(clip['event']['record']+3)
  else:assert clip['terminal']=='retire'
  segments[indices[pc]]={'source':pc,'clip':clip,'event':event,'next':nxt}
 return {'source_set':s.lock['aggregate_sha256'],'status':'source contract; native variant implementation pending',
         'constructor':0x8389,'roots':roots,'segments':segments,
         'actor':{'template':actor.hex(),'health':actor[14],'damage':actor[15],'width':actor[16],'height':actor[17],'cycles':actor[32],'category':actor[11]},
         'projectile':{'template':weapon.hex(),'health':weapon[14],'damage':weapon[15],'width':weapon[16],'height':weapon[17],'contact':weapon[13]&127},
         'spawn_x':list(s.read(0,0x8410,8)),'witnesses':list(s.witnesses.values())}
if __name__=='__main__':
 result=extract(Source());(ROOT/'reference/thrower.json').write_text(json.dumps(result,indent=2)+'\n');print(len(result['segments']),'typed segments')
