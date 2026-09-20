"""Recurring medium ground flame: four bank 1 constructors."""
from extract_animation import compile_clip
def extract(s):
 s.expect(1,0x8a8a,'21dc8a013000edb0');s.expect(1,0x8a7f,'fe14c03600')
 s.expect(1,0x8ab7,'3e0acde203dd360c09');s.expect(1,0x8acc,'dd360c0b')
 templates=[s.read(1,pc,48) for pc in (0x8adc,0x8b0c,0x8ca4,0x8c74)];segments=[]
 for t in templates:
  pc=int.from_bytes(t[30:32],"little")+5
  while True:
   clip=compile_clip(s,1,pc);event=clip['event'];segments.append(dict(source=pc,clip=clip,event={0x8ab7:0,0x8acc:1,0x8c4f:0,0x8c64:1}[event['address']] if event else 2))
   if not event:break
   pc=event['record']+3
 return dict(source_set=s.lock['aggregate_sha256'],templates=[t.hex() for t in templates],segments=segments,witnesses=list(s.witnesses.values()))
