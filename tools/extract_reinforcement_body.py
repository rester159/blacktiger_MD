"""Source graphs for the two bank-two reinforcement fighters."""
from extract_animation import compile_clip
ROOTS=[0x8a49,0x8aec,0x8afc,0x8d5d,0x8d65,0x8dab,0x8da3,0x8db3,0x8dcb,0x8dc3,0x8dd3,0x8a60,0x8aa6,0x8d6d,0x8d84,0x8ddb,0x8de3,0x8deb,0x8df3,0x8dfb,0x8e03,0x8e0e,0x8e41]
EVENTS=[0x83bc,0x83c1,0x8433,0x8518,0x861d,0x868c,0x86be,0x875d,0x87ab,0x87f9,0x8831]
def extract(s):
 segments=[];roots=[];choices=[];templates=[];shots=[]
 for profile,base in enumerate((0x8899,0xa07d)):
  t=s.read(2,base,48);templates.append(t.hex())
  pcs=[pc+(0x17e4 if i in (0,1,2,11,12) else 0x1804) if profile else pc for i,pc in enumerate(ROOTS)]
  pcs += [0xa2f0,0xa300] if profile else pcs[1:3]
  assert int.from_bytes(t[30:32],'little')+5==pcs[0]
  callbacks=[pc+(0x17b2 if i<2 else 0x17d0 if i==2 else 0x17da if i==3 else 0x17e4) if profile else pc for i,pc in enumerate(EVENTS)]
  indices={};pending=[]
  def intern(pc):
   if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
   return indices[pc]
  roots.append(list(map(intern,pcs)))
  while pending:
   pc=pending.pop(0);clip=compile_clip(s,2,pc);event=11;target=65535
   if clip['event']:
    e=clip['event'];event=callbacks.index(e['address'])
    if event in (2,3,6):target=intern(e['record']+3)
   segments[indices[pc]]=dict(source=pc,clip=clip,event=event,next=target)
  table=0xa678 if profile else 0x8e74
  choices.append([list(s.read(2,int.from_bytes(s.read(2,table+i*2,2),'little'),16)) for i in range(8)])
  group=[]
  for i in range(12):
   t=s.read(2,base+48+i*32,32);pc=int.from_bytes(t[30:32],'little')+5;clip=compile_clip(s,2,pc);assert clip['terminal']=='retire'
   group.append(dict(template=t.hex(),source=pc,clip=clip))
  shots.append(group)
 return dict(source_set=s.lock['aggregate_sha256'],roots=roots,segments=segments,choices=choices,templates=templates,shots=shots,health=[bytes.fromhex(t)[14] for t in templates],layers=[bytes.fromhex(t)[21] for t in templates],scores=[int(''.join(map(str,s.read(None,0x15bc+score-7,8)))) for score in (0x20,0x38)],witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 import json
 from arcade_source import Source,ROOT
 data=extract(Source());(ROOT/'reference/reinforcement_body.json').write_text(json.dumps(data,indent=2)+'\n');print(len(data['segments']),data['templates'])
