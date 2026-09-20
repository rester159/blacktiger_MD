"""Four constructors share the bank-zero flail-wielder controller."""
from extract_animation import compile_clip
PCS=[0xaf26,0xaf31,0xaf3c,0xafbf,0xb070,0xb094,0xb0b8,0xb0f0,0xb042,0xb059,0xb128,0xb130,0xb138,0xb140,0xb14b,0xb17e,0xb1c0,0xb1bd]
EVENTS=[0xab8b,0xabb3,0xac23,0xac53,0xace9,0xadb0,0xadef,0xae27,0xae95]
def extract(s):
 segments=[];pending=[];indices={};roots=[];templates=[]
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 for offset in (0,0x68e):
  t=[s.read(0,pc+offset,n) for pc,n in ((0xaea6,48),(0xaed6,48),(0xaf06,32))];templates.append([v.hex() for v in t])
  pcs=[int.from_bytes(v[30:32],'little')+5 for v in t[:2]]+[int.from_bytes(t[0][28:30],'little')+5]+[pc+offset for pc in PCS]
  roots.append(list(map(intern,pcs)))
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,0,pc);event=9;target=65535
  if clip['event']:
   e=clip['event'];address=e['address'];event=EVENTS.index(address-(0x68e if address>=0xb1c1 else 0))
   if event in (1,4,8):target=intern(e['record']+3)
  segments[indices[pc]]=dict(source=pc,clip=clip,event=event,next=target)
 return dict(source_set=s.lock['aggregate_sha256'],roots=roots,segments=segments,templates=templates,health=[bytes.fromhex(t[0])[21] for t in templates],scores=[int(''.join(map(str,s.read(None,0x15bc+score-7,8)))) for score in (0x20,0x30)],witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 import json
 from arcade_source import Source,ROOT
 data=extract(Source());(ROOT/'reference/flailer.json').write_text(json.dumps(data,indent=2)+'\n');print(len(data['segments']),data['health'],data['scores'],data['templates'])
