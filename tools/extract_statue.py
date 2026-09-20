"""Layered stationary caster, its directional shells, and explosion phases."""
from extract_animation import compile_clip
def extract(s):
 s.expect(0,0xb85b,'2163ba013000edb0')
 s.expect(0,0xb9b5,'dd3515cad8b9')
 s.expect(0,0xb9c4,'dd360e04')
 s.expect(0,0xb9e4,'16051e40cdd003')
 s.expect(0,0xb961,'dd3408dd7e08fe0d')
 t=s.read(0,0xba63,48);shot=s.read(0,0xba93,32);blast=s.read(0,0xbab3,48)
 pcs=[0xbafa,0xbafa,0xbae3,0xbb2b,0xbb11,0xbb50,0xbb45,0xbb91,0xbb5e,0xbb5b,0xbd84,0xbd9e,0xbe12]
 pcs += [s.word(0,0xbbc4+i*2)+5 for i in range(16)]
 segments=[];pending=[];indices={}
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,pcs));callbacks=[0xb890,0xb8e6,0xb961,0xb985,0xb995,0xb9a5,0xb9b5,0xba05]
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,0,pc);event=8;target=65535
  if clip['event']:
   e=clip['event'];event=callbacks.index(e['address'])
   if event not in (0,6,7):target=intern(e['record']+3)
  segments[indices[pc]]=dict(source=pc,clip=clip,event=event,next=target)
 return dict(source_set=s.lock['aggregate_sha256'],roots=roots,segments=segments,choices=list(s.read(0,0xbe13,16)),health=t[14],layers=t[21],reset_health=4,score=int(''.join(map(str,s.read(None,0x15bc+0x40-7,8)))),shot=shot.hex(),blast=blast.hex(),witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 import json
 from arcade_source import Source,ROOT
 data=extract(Source());(ROOT/'reference/statue.json').write_text(json.dumps(data,indent=2)+'\n');print(len(data['segments']),data['health'],data['layers'],data['score'])
