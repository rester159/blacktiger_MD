"""Locked-container content tables and constructor phases; opening effects are separate."""
from extract_animation import compile_clip
def extract(s):
 s.expect(None,0x304,'3e02183f')
 s.expect(None,0x24ac,'cd040310d6')
 s.expect(None,0x2475,'2128b8195e2356eb1130ea010800edb0')
 s.expect(None,0x2488,'2130ea3a09e00fe607')
 s.expect(None,0x2496,'2a08e07c0f850fe607')
 s.expect(1,0xacbe,'2a27e97ea7c0237ea7cae8ac237ea7ca8aadc3dbad')
 s.expect(1,0xacd3,'2a27e97ea7c0237ea7ca39ad237ea7ca8aadc3dbad')
 tables=[list(s.read(6,s.word(6,0xb828+2*r),8)) for r in range(8)]
 phases=[]
 for table in (0xae66,0xaf92,0xb0be):
  variants=[]
  for i in range(6):
   pc=s.word(1,table+2*i);t=s.read(1,pc,48)
   variants.append({'template':pc,'bytes':t.hex(),'contact':t[13],'initial':compile_clip(s,1,int.from_bytes(t[30:32],'little')+5),'collected':compile_clip(s,1,int.from_bytes(t[28:30],'little')+5)})
  phases.append(variants)
 handlers=[0x49b9,0x4a37,0x4a8f,0x4ae7,0x4b3f,0x49e3]
 coins=[]
 for pc in (0x4a80,0x4ad8,0x4b30,0x4b88):
  s.expect(None,pc,'2aa7f311')
  value=s.word(None,pc+4);coins.append(value)
  s.expect(None,pc+6,'1922a7f33e')
  index=s.read(None,pc+11,1)[0]
  # 4FAF updates the five decimal coin-display digits, not the score.
  digits=s.read(None,0x505e+index-4,5)
  assert int(''.join(map(str,digits)))==value
 s.expect(None,0x49b9,'21abf37ea7c835')
 s.expect(None,0x4a2c,'3ab6f3320ef4af3221f4c9')
 for pc in handlers:s.read(None,pc,0x2a if pc==0x49b9 else 0x54 if pc==0x49e3 else 0x58)
 return {'contact_handlers':handlers,'coin_values':coins,'source_set' :s.lock['aggregate_sha256'],'round_contents':tables,'phases':phases,'scope':'Content shuffle, constructor phases and contact effects. Native contact kernel is not yet connected to gameplay; inventory, phase timing, trap actors and persistence still need integration.','witnesses':list(s.witnesses.values())}
