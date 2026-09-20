"""Four falling-seed families share gravity, splitting, walking and hit logic."""
from extract_animation import compile_clip
PROFILES=[
 (3,0xacbe,[0xad1e,0xad26,0xad42,0xad7f,0xae21,0xaf71,0xb0c1,0xb0f6,0xb101,0xb139,0xadb7,0xadec,0xb0fe],[0xaaf4,0xab12,0xab1c,0xab54,0xabce,0xabde,0xac2e,0xac5e,0xac8a],0x10),
 (3,0xb35e,[0xb3be,0xb3c6,0xb3e2,0xb41f,0xb4c1,0xb611,0xb761,0xb796,0xb7a1,0xb7d9,0xb457,0xb48c,0xb79e],[0xb194,0xb1b2,0xb1bc,0xb1f4,0xb26e,0xb27e,0xb2ce,0xb2fe,0xb32a],0x18),
 (7,0xa5bd,[0xa61d,0xa625,0xa641,0xa67e,0xa720,0xa776,0xa7cc,0xa801,0xa80c,0xa844,0xa6b6,0xa6eb,0xa809],[0xa3f7,0xa415,0xa41f,0xa457,0xa4d1,0xa4e1,0xa531,0xa561,0xa58d],0x18),
 (3,0xbaad,[0xbb0d,0xbb15,0xbb31,0xbb6e,0xbc10,0xbc66,0xbcbc,0xbd3d,0xbd48,0xbd80,0xbba6,0xbbdb,0xbd45],[0xb834,0xb852,0xb85c,0xb894,0xb90e,0xb93b,0xb9f0,0xba51,0xba7d,None,0xb91e,0xba1a],0x18)]
def extract(s):
 segments=[];roots=[];templates=[];scores=[]
 for bank,base,pcs,callbacks,score in PROFILES:
  s.expect(bank,callbacks[8],'3a0df447dd7e1590')
  ts=[s.read(bank,base+i*32,32) for i in range(3)];templates.append([t.hex() for t in ts])
  assert [int.from_bytes(t[30:32],'little')+5 for t in ts]==[pcs[i] for i in (0,10,11)]
  pending=[];indices={}
  def intern(pc):
   if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
   return indices[pc]
  roots.extend(map(intern,pcs))
  if base==0xbaad:jump_roots=list(map(intern,(0xbcf1,0xbcfc,0xbd07,0xbd12)))
  while pending:
   pc=pending.pop(0);clip=compile_clip(s,bank,pc);event=9;target=65535
   if clip['event']:
    e=clip['event'];event=callbacks.index(e['address'])
    if event in (1,2,4,5,11):target=intern(e['record']+3)
   segments[indices[pc]]=dict(bank=bank,source=pc,clip=clip,event=event,next=target)
  scores.append(int(''.join(map(str,s.read(None,0x15bc+score-7,8)))))
 return dict(source_set=s.lock['aggregate_sha256'],roots=roots,jump_roots=jump_roots,choices=list(s.read(3,0xbd9a,16)),segments=segments,templates=templates,health=[bytes.fromhex(t[0])[21] for t in templates],scores=scores,witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 import json
 from arcade_source import Source,ROOT
 data=extract(Source());(ROOT/'reference/crawler.json').write_text(json.dumps(data,indent=2)+'\n');print(len(data['segments']),data['health'],data['scores'])
