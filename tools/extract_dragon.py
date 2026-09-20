"""Shared bank-three dragon body graphs; source bytes never execute on Genesis."""
from extract_animation import compile_clip
ROOTS=[0x8369,0x8374,0x838e,0x83a0,0x83b2,0x83bd,0x90c5,0x87ab,0x9b07,0x9aed,0x979e,0x97a1,0x983a,0x98d3,0x98f8]
EVENTS=[0x8075,0x8093,0x80b4,0x8178,0x81b4,0x81e1,0x828f,0x8299,0x82c9,0x9715,0x9778,0x978e,0x5a4f,0x9aa9,0x9ad7,0x9cb8,0x9ce6,0x9992,0x9b99,0x8215,0x81d1]
CONTINUE={0,1,3,4,5,6,7,10,11,14,16}
def extract(s):
 segments=[];indices={};pending=[]
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,ROOTS));choices=[]
 for base in (0x82e1,0x9a21,0x9c30):
  choices.append([[intern(s.word(3,s.word(3,base+i*2)+j*2)) for j in range(16)] for i in range(4)])
 aims=[intern(s.word(3,0x83c8+i*2)) for i in range(16)]
 distances=[intern(s.word(3,0x9ae1+i*2)) for i in range(6)]
 assert s.read(3,0x9ae1,12)==s.read(3,0x9cf0,12)
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,3,pc);e=clip['event'];assert e,(hex(pc),clip)
  event=EVENTS.index(e['address']);targets=[65535,65535]
  if event in CONTINUE:targets[0]=intern(e['record']+3)
  if event==11:targets[1]=intern(e['record']+6)
  segments[indices[pc]]=dict(source=pc,clip=clip,event=event,next=targets)
 templates=[s.read(3,pc,48) for pc in (0x8045,0x9962,0x9b69)]
 return dict(source_set=s.lock['aggregate_sha256'],roots=roots,segments=segments,choices=choices,aims=aims,distances=distances,templates=[t.hex() for t in templates],health=[t[14] for t in templates],layers=[t[21] for t in templates],score=int(''.join(map(str,s.read(None,0x15bc+0x70-7,8)))),witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 import json
 from arcade_source import Source,ROOT
 data=extract(Source());(ROOT/'reference/dragon.json').write_text(json.dumps(data,indent=2)+'\n');print(len(data['segments']),data['score'])
