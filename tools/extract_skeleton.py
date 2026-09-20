"""Compile three skeleton variants into native animation segments and typed transitions."""
import json
from arcade_source import Source,ROOT
from extract_animation import compile_clip
CALLBACKS=[
 [0x942e,0x9456,0x94c7,0x94f7,0x9584,0x964b,0x968a,0x96c2,0x9730],
 [0x9bc6,0x9bee,0x9c5f,0x9c8f,0x9d25,0x9dec,0x9e2b,0x9e63,0x9f0d],
 [0xa39d,0xa3c5,0xa436,0xa466,0xa4fc,0xa5c3,0xa602,0xa63a,0xa6e4]]
# initial, walk R/L, approach R/L, swing R/L, weapon R/L, jump R/L,
# retreat R/L, falling R/L, death R/L, damage entry.
ROOTS=[
 [0x9791,0x9847,0x9794,0x9980,0x98fa,0x9a58,0x9a34,0x9ab4,0x9a7c,0x9af4,0x9aec,0x9a1d,0x9a06,0x9b04,0x9afc,0x9b42,0x9b0f,0x9b0c],
 [0x9f6e,0xa024,0x9f71,0xa15a,0xa0d7,0xa22f,0xa20b,0xa28b,0xa253,0xa2cb,0xa2c3,0xa1f4,0xa1dd,0xa2db,0xa2d3,0xa319,0xa2e6,0xa2e3],
 [0xa745,0xa7fb,0xa748,0xa931,0xa8ae,0xaa06,0xa9e2,0xaa62,0xaa2a,0xaaa2,0xaa9a,0xa9cb,0xa9b4,0xaab2,0xaaaa,0xaaf0,0xaabd,0xaaba]]
TEMPLATES=[0x9741,0x9f1e,0xa6f5]
CONSTRUCTORS=[0x93ed,0x9b85,0xa35c]

def extract(s):
 segments=[];profiles=[]
 for variant in range(3):
  callbacks={pc:i+1 for i,pc in enumerate(CALLBACKS[variant])};indices={};pending=[]
  def intern(pc):
   if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
   return indices[pc]
  roots=list(map(intern,ROOTS[variant]))
  t=s.read(0,TEMPLATES[variant],48)
  assert s.word(0,TEMPLATES[variant]+30)+5==ROOTS[variant][0]
  assert s.word(0,TEMPLATES[variant]+28)+5==ROOTS[variant][-1]
  while pending:
   pc=pending.pop(0);clip=compile_clip(s,0,pc);event=0;nxt=65535
   if clip['terminal']=='event':
    event=callbacks[clip['event']['address']]
    if event in (2,5,9):nxt=intern(clip['event']['record']+3)
   elif clip['terminal']=='retire':event=10
   segments[indices[pc]]={'variant':variant,'source':pc,'clip':clip,'event':event,'next':nxt}
  score_bytes=s.read(None,0x15bc+(0x20 if variant==0 else 0x30)-7,8)
  profiles.append({'roots':roots,'durability':t[21],'guard':t[35],'variant':variant,'score':int(''.join(map(str,score_bytes)))})
 return {'source_set':s.lock['aggregate_sha256'],'profiles':profiles,'segments':segments,'constructors':CONSTRUCTORS,'callback_addresses':CALLBACKS,'witnesses':list(s.witnesses.values())}
if __name__=='__main__':
 d=extract(Source());(ROOT/'reference/skeleton.json').write_text(json.dumps(d,indent=2)+'\n');print(len(d['segments']),'segments',d['profiles'])
