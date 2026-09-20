"""Compile the stacked boss controller's animation graph into native records."""
from extract_animation import compile_clip
ROOTS=[0xa34b,0xa368,0xa370,0xa3b4,0xa3d2,0xa378,0xa396,0xa42c,0xa44a,0xa3f0,0xa40e,0xa468,0xa473,0xa481,0xa47e]
EVENTS=[0x9fa6,0x9fd5,0xa160,0xa1f9,0xa0b0,0x5a4f]
def extract(s):
 segments=[];pending=[];indices={}
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,ROOTS))
 while pending:
  pc=pending.pop(0);c=compile_clip(s,4,pc);assert c['terminal']=='event'
  e=c['event'];event=EVENTS.index(e['address']);nxt=[65535,65535]
  if event in (0,2,3):
   nxt[0]=intern(e['record']+3)
   if event!=3:nxt[1]=intern(e['record']+6)
  segments[indices[pc]]={'source':pc,'clip':c,'event':event,'next':nxt}
 return {'source_set':s.lock['aggregate_sha256'],'roots':roots,'segments':segments,'choices':list(s.read(4,0xa4c0,16)),'witnesses':list(s.witnesses.values())}
