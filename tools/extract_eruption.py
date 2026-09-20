"""Recurring medium ground flame: bank 1 8A5D."""
from extract_animation import compile_clip
def extract(s):
 s.expect(1,0x8a8a,'21dc8a013000edb0');s.expect(1,0x8a7f,'fe14c03600')
 s.expect(1,0x8ab7,'3e0acde203dd360c09');s.expect(1,0x8acc,'dd360c0b')
 t=s.read(1,0x8adc,48);segments=[];pc=s.word(1,0x8afa)+5
 while True:
  clip=compile_clip(s,1,pc);event=clip['event'];segments.append(dict(source=pc,clip=clip,event={0x8ab7:0,0x8acc:1}[event['address']] if event else 2))
  if not event:break
  pc=event['record']+3
 return dict(source_set=s.lock['aggregate_sha256'],template=t.hex(),segments=segments,witnesses=list(s.witnesses.values()))
