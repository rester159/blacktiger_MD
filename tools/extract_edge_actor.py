"""Bank-four edge-entry caster body and its two aimed projectile profiles."""
from extract_animation import compile_clip
BODY_ROOTS=[0xaa7c,0xaaa7,0xaad2,0xaae5,0xaaf8,0xab0b,0xab1e,0xab31,0xab44,0xab57,0xab6a,0xab7d,0xaba0,0xabc3,0xabf1,0xabe6,0xabff,0xac43,0xae78,0xaea8,0xaee3,0xaed8,0xadfe,0xae3b,0xab90,0xab98,0xac87,0xacda,0xad2d,0xad90]
EVENTS=[0xa564,0xa568,0xa5d2,0xa5fa,0xa622,0xa64a,0xa672,0xa6a0,0xa6f4,0xa726,0xa73e,0xa79e,0xa7c6,0xa7e0,0xa81f,0xa93a,0xa9b4]
def extract(s):
 def graph(pcs,events,continuations):
  segments=[];pending=[];indices={}
  def intern(pc):
   if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
   return indices[pc]
  roots=list(map(intern,pcs))
  while pending:
   pc=pending.pop(0);clip=compile_clip(s,4,pc);event=len(events);target=65535
   if clip['event']:
    e=clip['event'];event=events.index(e['address'])
    if event in continuations:target=intern(e['record']+3)
   segments[indices[pc]]=dict(source=pc,clip=clip,event=event,next=target)
  return roots,segments
 body=s.read(4,0xaa0c,48);templates=[s.read(4,p,32) for p in (0xaa3c,0xaa5c)]
 roots,segments=graph(BODY_ROOTS+[s.word(4,0xa9d0+i*2) for i in range(10)]+[0xabfc],EVENTS,{2,3,4,5,6,7,8,12,13,15})
 shot_pcs=[s.word(4,p+i*2)+5 for p in (0xaeee,0xb0da) for i in range(17)]+[int.from_bytes(t[28:30],'little')+add for t in templates for add in (0,5)]
 shot_roots,shot_segments=graph(shot_pcs,[0xa9ea],{0})
 return dict(source_set=s.lock['aggregate_sha256'],roots=roots,segments=segments,shot_roots=shot_roots,shot_segments=shot_segments,template=body.hex(),shot_templates=[t.hex() for t in templates],choices=[list(s.read(4,s.word(4,0xb2cb+i*2),16)) for i in range(8)],attacks=list(s.read(4,0xb328,16)),health=body[14],layers=body[21],score=int(''.join(map(str,s.read(None,0x15bc+0x40-7,8)))),witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 import json
 from arcade_source import Source,ROOT
 data=extract(Source());(ROOT/'reference/edge_actor.json').write_text(json.dumps(data,indent=2)+'\n');print(len(data['segments']),len(data['shot_segments']),data['health'],data['layers'],data['score'])
