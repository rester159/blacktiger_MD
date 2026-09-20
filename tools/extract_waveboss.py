"""Bank 1 98A3/98E8: large layered bosses and ground-wave seeds."""
from extract_animation import compile_clip
ROOTS=[0x9b9f,0x9baa,0x9bad,0x9d7c,0x9d3d,0x9cfe,0x9bef,0x9bc4,0x9c31,0x9c1a,0x9c5d,0x9c48,0x9e4d,0x9d7f,0x9f3f,0x9f1b,0x9c72,0x9cb8]
EVENTS=[0x992d,0x9967,0x9977,0x9a00,0x9a74,0x9a8f,0x9aab,0x9b07,0x5a4f,0x9945,0x99d0,0x99e0,0x99f0]
def extract(s):
 templates=[s.read(1,pc,n) for pc,n in ((0x9b1f,48),(0x9b4f,48),(0x9b7f,32))]
 segments=[];pending=[];indices={}
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,ROOTS))
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,1,pc);event=13;nxt=[65535,65535]
  if clip['event']:
   e=clip['event'];event=EVENTS.index(e['address'])
   if event in (0,1,3,4,5,7):nxt[0]=intern(e['record']+3)
   if event==5:nxt[1]=intern(e['record']+6)
  segments[indices[pc]]=dict(source=pc,clip=clip,event=event,next=nxt)
 return dict(source_set=s.lock['aggregate_sha256'],templates=[t.hex() for t in templates],contact_shapes=[[t[32] if t[32]<128 else t[32]-256,t[33] if t[33]<128 else t[33]-256,t[34],t[35],t[16],t[17]] for t in templates[:2]],roots=roots,segments=segments,choices=[list(s.read(1,pc,16)) for pc in (0x9f63,0x9f73)],health=[t[14] for t in templates[:2]],layers=[t[21] for t in templates[:2]],scores=[int(''.join(map(str,s.read(None,0x15bc+score-7,8)))) for score in (0x90,0xa8)],witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 import json
 from arcade_source import Source,ROOT
 data=extract(Source());(ROOT/'reference/waveboss.json').write_text(json.dumps(data,indent=2)+'\n');print(len(data['segments']),data['health'],data['layers'],data['scores'])
