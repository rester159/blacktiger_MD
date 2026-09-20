"""Common source death-drop distributions, currency clips, and random recurrence."""
import json
from arcade_source import Source,ROOT
from extract_animation import compile_clip

def extract(s):
 s.expect(None,0x54e9,'dd7e0b876f260011da56195e23563a09e0e61f26006f197ea7c8')
 s.expect(None,0x5533,'dd6601dd6e0211080019fd7401fd7502dd6603dd6e04fd7403fd7504')
 s.expect(None,0x9b9,'2a08e0545d29197c83672208e0')
 s.expect(None,0x1a0,'21c3012208e0')
 tables=[list(s.read(None,s.word(None,0x56da+2*i),32)) for i in range(28)]
 assert all(0<=x<=7 for row in tables for x in row)
 kinds=[]
 for k in range(7):
  at=s.word(None,0x5558+k*2);t=s.read(None,at,32)
  assert t[13]==k+3 and t[23]==0
  handler=s.word(None,0x4751+2*t[13])
  if k==0:
   s.expect(None,handler+43,'2aa7f32322a7f3');coins=1
  else:
   s.expect(None,handler+43,'2aa7f311');coins=s.word(None,handler+47);s.expect(None,handler+49,'1922a7f3')
  clip=compile_clip(s,None,int.from_bytes(t[30:32],'little')+5)
  assert clip['terminal']=='retire' and sum(f['duration'] for f in clip['frames'])==240
  consumed=compile_clip(s,None,int.from_bytes(t[28:30],'little')+5)
  assert not consumed['frames'] and consumed['terminal']=='retire'
  kinds.append({'kind':k+1,'template':t.hex(),'template_address':at,'handler':handler,'coins':coins,'clip':clip})
 return {'source_set':s.lock['aggregate_sha256'],'tables':tables,'kinds':kinds,'seed':451,'rng_multiplier':259,'witnesses':list(s.witnesses.values())}
if __name__=='__main__':
 d=extract(Source());(ROOT/'reference/loot.json').write_text(json.dumps(d,indent=2)+'\n');print('currency values',[k['coins'] for k in d['kinds']])
