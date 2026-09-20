"""Development contract for the third recurring walker; not runtime Z80 code."""
import json
from arcade_source import Source,ROOT
from extract_animation import compile_clip
ROOTS=[0x9171,0x920b,0x9193,0x92ae,0x9283,0x931b,0x9313,0x9323,0x9357,
       0x92e6,0x92d9,0x9303,0x92f3,0x930b,0x92fb,0x933d,0x935a,0x938d]
EVENTS={0x8a55:'disable_contact',0x8a5c:'enable_contact',0x8a6d:'choose_walk_or_throw',
        0x8b65:'walk_step',0x8c30:'fall_step',0x8c68:'death_drop',0x8aff:'throw',
        0x8be0:'jump_start',0x8be4:'jump_step',0x8c80:'projectile_hit'}
def extract(s):
 s.expect(0,0x89e3,'21978c013000edb0')
 s.expect(0,0x8b09,'21c78c012000edb0')
 s.expect(0,0x8acb,'cdb205c604e60ffe09d27b8a')
 actor=s.read(0,0x8c97,48);weapon=s.read(0,0x8cc7,32)
 segments=[];indices={};pending=[]
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,ROOTS+[s.word(0,0x8ce7+2*i)+5 for i in range(32)]+[0x93d8]))
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,0,pc);event='retire';nxt=None
  if clip['terminal']=='event':
   event=EVENTS[clip['event']['address']]
   if event in ('disable_contact','enable_contact','walk_step'):nxt=intern(clip['event']['record']+3)
  else:assert clip['terminal']=='retire'
  segments[indices[pc]]={'source':pc,'clip':clip,'event':event,'next':nxt}
 return {'source_set':s.lock['aggregate_sha256'],'status':'typed source contract for native variant',
         'constructor':0x89c6,'roots':roots,'segments':segments,
         'actor':{'template':actor.hex(),'health':actor[14],'damage':actor[15],'width':actor[16],'height':actor[17],'cycles':actor[32],'category':actor[11]},
         'projectile':{'template':weapon.hex(),'health':weapon[14],'damage':weapon[15],'width':weapon[16],'height':weapon[17],'contact':weapon[13]&127},
         'score':int(''.join(map(str,s.read(None,0x15bc+actor[23]-7,8)))),'spawn_x':list(s.read(0,0x8a4d,8)),'witnesses':list(s.witnesses.values())}
if __name__=='__main__':
 result=extract(Source());(ROOT/'reference/spitter.json').write_text(json.dumps(result,indent=2)+'\n');print(len(result['segments']),'typed segments')
