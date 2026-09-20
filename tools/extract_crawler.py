"""Falling seed and its three ground-crawling bodies (bank 3 AAB3)."""
from extract_animation import compile_clip
def extract(s):
 s.expect(3,0xaabf,'21beac012000edb0')
 s.expect(3,0xac8a,'3a0df447dd7e1590')
 templates=[s.read(3,pc,32) for pc in (0xacbe,0xacde,0xacfe)]
 pcs=[0xad1e,0xad26,0xad42,0xad7f,0xae21,0xaf71,0xb0c1,0xb0f6,0xb101,0xb139,0xadb7,0xadec,0xb0fe]
 callbacks=[0xaaf4,0xab12,0xab1c,0xab54,0xabce,0xabde,0xac2e,0xac5e,0xac8a]
 segments=[];pending=[];indices={}
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,pcs))
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,3,pc);event=9;target=65535
  if clip['event']:
   e=clip['event'];event=callbacks.index(e['address'])
   if event in (1,2,4,5):target=intern(e['record']+3)
  segments[indices[pc]]=dict(source=pc,clip=clip,event=event,next=target)
 return dict(source_set=s.lock['aggregate_sha256'],roots=roots,segments=segments,templates=[t.hex() for t in templates],health=templates[0][21],score=int(''.join(map(str,s.read(None,0x15bc+0x10-7,8)))),witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 import json
 from arcade_source import Source,ROOT
 data=extract(Source());(ROOT/'reference/crawler.json').write_text(json.dumps(data,indent=2)+'\n');print(len(data['segments']),data['health'],data['score'])
