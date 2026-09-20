"""Two small flying actors previously misclassified as a treasure chest."""
from extract_animation import compile_clip
def extract(s):
 s.expect(2,0xacf6,'21c9ad014000edb0')
 s.expect(2,0xad2d,'2a27e93e02b677')
 s.expect(2,0xad3d,'dd3408dd7e08fe10cab5ad')
 t=s.read(2,0xadc9,64);pcs=[int.from_bytes(t[n+30:n+32],'little')+5 for n in (0,32)]+[0xaff5,0xb4a0]
 pcs += [s.word(2,0xb040+2*i) for i in range(16)]+[s.word(2,0xb4b7+2*i) for i in range(8)]
 segments=[];pending=[];indices={}
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,pcs))
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,2,pc);event=3;target=65535
  if clip['terminal']=='event':
   e=clip['event'];event=[0xad39,0xad3d,0xada4].index(e['address'])
   if event==2:target=intern(e['record']+3)
  segments[indices[pc]]={'source':pc,'clip':clip,'event':event,'next':target}
 return {'source_set':s.lock['aggregate_sha256'],'roots':roots,'segments':segments,'choices':list(s.read(2,0xb66f,16)),'score':int(''.join(map(str,s.read(None,0x15bc+t[23]-7,8)))),'witnesses':list(s.witnesses.values())}
