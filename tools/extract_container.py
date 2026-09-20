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
 segments=[];pending=[];indices={}
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,[0xb21a,0xb24c,0xb28a,0xb26b,0xb222,0xb237,0xb22a,0xb244]))
 trap_templates=[s.read(1,0x831a+32*i,32) for i in range(6)]
 trap_roots=[intern(int.from_bytes(t[30:32],'little')+5) for t in trap_templates]
 wave_templates=[s.read(1,0x868e+32*i,32) for i in range(6)]
 wave_roots=[intern(int.from_bytes(t[30:32],'little')+5) for t in wave_templates]
 callbacks=[0xae12,0xae48,0xae2a,0x82d4,0x82f9,0x8309]
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,1,pc);event=6;target=65535
  if clip['event']:
   event=callbacks.index(clip['event']['address']);target=intern(clip['event']['record']+3)
  segments[indices[pc]]={'source':pc,'clip':clip,'event':event,'next':target}
 return {'wave_roots':wave_roots,'wave_templates':[t.hex() for t in wave_templates],'roots':roots,'trap_roots':trap_roots,'segments':segments,'trap_templates':[t.hex() for t in trap_templates],'contact_handlers':handlers,'coin_values':coins,'source_set' :s.lock['aggregate_sha256'],'round_contents':tables,'phases':phases,'scope':'Content shuffle, constructor phases and contact effects. Includes native phase and trap animation graphs. Startup inventory, key acquisition and full lifecycle persistence still require a source port.','witnesses':list(s.witnesses.values())}
