"""Bank 1 92E6 and 8D33: recurring teleporter and its custom damage phases."""
from extract_animation import compile_clip
def extract(s):
 s.expect(1,0x9303,'217394013000edb0');s.expect(1,0x9419,'cb38')
 templates=[s.read(1,address,48) for address in (0x9473,0x8ec0)]
 t=templates[0]
 pcs=[0x94a3,0x951d,0x94a6,0x967a,0x9594,0x96fb,0x9615,0x9691,0x95ab,0x97c5,0x9760,0x9860,0x982d,0x982a]
 callbacks=[0x9344,0x9360,0x9370,0x9380,0x939c,0x93c5,0x93ff,0x940f]
 pcs += [0x8ef0,0x8f65,0x8ef3,0x90bd,0x8fd7,0x913e,0x9058,0x90d4,0x8fee,0x9208,0x91a3,0x92a3,0x9270,0x926d]
 callbacks += [0x8d91,0x8dad,0x8dbd,0x8dcd,0x8de9,0x8e12,0x8e4c,0x8e5c]
 assert s.read(1,0x9893,16)==s.read(1,0x92d6,16)
 s.expect(1,0x8043,'211a8301c000edb0');s.expect(1,0x8084,'110800');s.expect(1,0x80c5,'110800')
 segments=[];pending=[];indices={}
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,pcs))
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,1,pc);event=8;target=65535
  if clip['event']:
   e=clip['event'];event=callbacks.index(e['address'])%8
   if event in (1,2,4,6):target=intern(e['record']+3)
  segments[indices[pc]]=dict(source=pc,clip=clip,event=event,next=target)
 return dict(source_set=s.lock['aggregate_sha256'],roots=roots,segments=segments,templates=[t.hex() for t in templates],positions=[list(s.read(1,0x9893+2*i,2)) for i in range(8)],health=[t[21] for t in templates],score=int(''.join(map(str,s.read(None,0x15bc+0x40-7,8)))),witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 import json
 from arcade_source import Source,ROOT
 data=extract(Source());(ROOT/'reference/teleporter.json').write_text(json.dumps(data,indent=2)+'\n');print(len(data['segments']),data['health'],data['score'])
