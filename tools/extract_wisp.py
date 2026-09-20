"""Compile bank-2 A6F8 movement clips into native conditional transitions."""
from extract_animation import compile_clip

def extract(s):
 t=s.read(2,0xa7c7,48)
 assert t[14]==1 and t[16:18]==bytes([12,12]) and t[23]==0
 assert int.from_bytes(t[30:32],'little')+5==0xa7f7
 hit=compile_clip(s,2,int.from_bytes(t[28:30],'little')+5)
 assert not hit['frames'] and hit['event']['address']==0xa7b3
 roots=[0xa7f7,0xa825,0xa946,0xa915,0xab88,0xaa36,0xaa67]
 callbacks=[0xa739,0xa752,0xa77a,0xa78d,0xa7a0,0xa7b3]
 segments=[];indices={};pending=[]
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 native_roots=list(map(intern,roots))
 while pending:
  pc=pending.pop(0);c=compile_clip(s,2,pc);assert c['terminal']=='event'
  e=c['event'];event=callbacks.index(e['address']);nxt=[65535,65535]
  if event==0:nxt[0]=intern(e['record']+3)
  if event==1:nxt=[intern(e['record']+3),intern(e['record']+6)]
  segments[indices[pc]]={'clip':c,'event':event,'next':nxt}
 s.expect(2,0xa739,'3a04f4c646dd9604fe8cda7aa7')
 s.expect(2,0xa7b3,'3e08dd770cdd360e013e16cde20321f7a7c3e632')
 return {'source_set':s.lock['aggregate_sha256'],'roots':native_roots,'segments':segments,'witnesses':list(s.witnesses.values())}
