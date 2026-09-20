"""Compile the bank-zero recurring walker into native typed transitions."""
from extract_animation import compile_clip
ROOTS=[0x81c1,0x825b,0x81e3,0x82fe,0x82d3,0x8331,0x8329,0x8339,0x8353]
EVENTS=[0x808f,0x8096,0x80a7,0x80d7,0x8145,0x817d]
def extract(s):
 s.expect(0,0x801d,'219181013000edb0')
 t=s.read(0,0x8191,48);segments=[];pending=[];indices={}
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,ROOTS))
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,0,pc);event=6;nxt=65535
  if clip['terminal']=='event':
   event=EVENTS.index(clip['event']['address'])
   if event in (0,1,3,5):nxt=intern(clip['event']['record']+3)
  else:assert clip['terminal']=='retire'
  segments[indices[pc]]={'clip':clip,'next':nxt,'event':event,'source':pc}
 return {'source_set':s.lock['aggregate_sha256'],'segments':segments,'roots':roots,'lifetime':t[32],'health':t[14],'score':int(''.join(map(str,s.read(None,0x15bc+t[23]-7,8)))),'spawn_x':list(s.read(0,0x8087,8)),'witnesses':list(s.witnesses.values())}
