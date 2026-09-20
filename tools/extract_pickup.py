"""Placed time-extension and screen-attack items; source target pool filters."""
from extract_animation import compile_clip

def extract(s):
 variants=[]
 for pc,template in ((0xb4af,0xb4ec),(0xb515,0xb552)):
  t=s.read(4,template,32);clip=compile_clip(s,4,int.from_bytes(t[30:32],'little')+5)
  consumed=compile_clip(s,4,int.from_bytes(t[28:30],'little')+5)
  assert clip['terminal']=='loop' and len(clip['frames'])==1 and not consumed['frames'] and consumed['terminal']=='retire'
  assert t[23]==0
  variants.append({'constructor':pc,'contact':t[13],'half_width':t[16],'half_height':t[17],'clip':clip})
 s.expect(None,0x4d8c,'1130002ab1f3197dd6603802246f22b1f3')
 s.expect(4,0xb5ba,'dd7e0df680ee80a7280afe2a2806fe342802')
 s.expect(4,0xb5ed,'dd7e0df680ee80a7280afe232806fe262802')
 return {'source_set':s.lock['aggregate_sha256'],'variants':variants,'time_seconds':30,'screen_contacts':{'32':[0,42,52],'48':[0,35,38]},'witnesses':list(s.witnesses.values())}
