"""Dragon orb, impact explosion and ground-flame seed animation graphs."""
from extract_animation import compile_clip
from arcade_source import Source,ROOT
import json
def extract(s):
 segments=[];indices={};pending=[]
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=[intern(s.word(3,0x9e26+i*2)+5) for i in range(16)]
 roots += list(map(intern,(0xa1a6,0xa1e4,0xa079,0xa094,0xa093)))
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,3,pc,raw_jump_frames=True);event=5;nxt=[65535,65535]
  if pc==0xa07c:
   # A malformed raw jump reads the callback bytes as a zero-duration frame.
   # Every possible 16-bit Y retires before that 256-tick frame can end.
   assert clip['frames'][4]['duration']==0 and clip['frames'][4]['vy']==-110
   def active(y):return not(y>>8) or ((y-48)&255)>=160
   assert all(any(not active((y-110*n)&65535) for n in range(1,9)) for y in range(65536))
   clip=dict(frames=clip['frames'][:5],loop=None,terminal='retire',event=None)
  if clip['event']:
   e=clip['event'];event=[0x9e46,0x9e69,0x9ec7,0x9ed0,0xa190].index(e['address']);nxt[0]=intern(e['record']+3)
   if event==4:nxt[1]=intern(e['record']+4)
  segments[indices[pc]]=dict(source=pc,clip=clip,event=event,next=nxt)
 return dict(source_set=s.lock['aggregate_sha256'],segments=segments,roots=roots,templates=[s.read(3,pc,n).hex() for pc,n in ((0x9dd6,32),(0xa170,32),(0x9df6,48))],witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 data=extract(Source());(ROOT/'reference/dragon_shot.json').write_text(json.dumps(data,indent=2)+'\n');print(len(data['segments']))
