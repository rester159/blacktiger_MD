"""Layered flying hunter and its boss variant, bank 1 9F83/9FC4."""
from extract_animation import compile_clip
def extract(s):
 s.expect(1,0xa0e9,'dd360e14');s.expect(1,0xa131,'dd360e2e')
 s.expect(1,0x9f8f,'2159a2013000edb0');s.expect(1,0x9fd8,'2189a2013000edb0')
 templates=[s.read(1,pc,n) for pc,n in ((0xa259,48),(0xa289,48),(0xa2b9,32),(0xa2d9,48))]
 word=lambda raw,offset:int.from_bytes(raw[offset:offset+2],'little')
 pcs=[word(templates[0],30)+5,word(templates[1],30)+5,word(templates[0],28)+5,word(templates[1],28)+5,0xaa76,0xa3e0,0xa3fa,0xa42a,0xa45a,0xa48a,0xac44,word(templates[3],30)+5]
 pcs += [s.word(1,0xa4ba+2*i) for i in range(16)]
 pcs += [s.word(1,0xa8f2+2*i) for i in range(16)]
 pcs += [s.word(1,0xaa84+2*i)+5 for i in range(16)]
 pcs += [word(templates[2],28)+5]
 callbacks=[0xa00d,0xa019,0xa02d,0xa04b,0xa0e0,0xa11d,0xa168,0xa1d9,0xa206,0x5a4f]
 segments=[];pending=[];indices={}
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,pcs))
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,1,pc);event=10;target=65535
  if clip['event']:
   e=clip['event'];event=callbacks.index(e['address'])
   if event not in (3,9):target=intern(e['record']+3)
  segments[indices[pc]]=dict(source=pc,clip=clip,event=event,next=target)
 return dict(source_set=s.lock['aggregate_sha256'],roots=roots,segments=segments,templates=[t.hex() for t in templates],choices=list(s.read(1,0xacae,16)),health=[t[14] for t in templates],layers=[t[21] for t in templates[:2]],reset_health=[20,46],score=int(''.join(map(str,s.read(None,0x15bc+0x60-7,8)))),witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 import json
 from arcade_source import Source,ROOT
 data=extract(Source());(ROOT/'reference/hunter.json').write_text(json.dumps(data,indent=2)+'\n');print(len(data['segments']),data['health'],data['layers'],data['score'])
