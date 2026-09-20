"""Check every compiled frame callback/layout and behavior route against the established family tables."""
import json,struct,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from run_rom import Runner
rom=(ROOT/'out/release/rom.bin').read_bytes();r=Runner(ROOT/'out/release/rom.bin');symbols=r.symbols;r.close()
meta=json.loads((ROOT/'reports/assets.json').read_text())
routes=[('pair','pair_frame',1),('edge_spawn','edge_actor_frame',2),('reinforcement','reinforcement_body_frame',2),('flailer','flailer_frame',2),('dragon','dragon_frame',3),('waveboss','waveboss_frame',4),('eruption','eruption_frame',2),('teleporter','teleporter_frame',2),('hunter','hunter_frame',2),('crawler','crawler_frame',1),('statue','statue_frame',2),('boulder','boulder_frame',2),('layered_boss','boss_frame',2),('stone','boss_frame',2),('zombie','zombie_frame',2),('wisp','wisp_frame',2),('emerge','emerge_frame',2),('sentry','sentry_frame',2),('skeleton','skeleton_frame',2)]
counts={}
for d in meta['actor_definitions']:
 i=d['id'];function=None;layout=0
 if d['kind']==5:function,layout='container_frame',2
 else:
  for family,name,style in routes:
   value=rom[symbols[family+'_kinds']+i]
   if (value!=255 if family=='skeleton' else value!=0):function,layout=name,style;break
  else:
   if d['kind']==9:function,layout='hidden_frame',1
   elif d['npc_kind']:function,layout='npc_frame',2
 behaviors=['edge_spawn','reinforcement','flailer','waveboss','eruption','teleporter','hunter','crawler','statue','boulder','stone','zombie','wisp','emerge','hazard']
 behavior=next((n+1 for n,family in enumerate(behaviors) if ((d['bank'],d['address'])==(1,0xb2a9) if family=='hazard' else rom[symbols[family+'_kinds']+i])),0)
 if function=='boss_frame':behavior=11 # Layered bosses are dispatched before the common culling path.
 expected=(symbols[function] if function else 0,layout,behavior)
 actual=struct.unpack_from('>IHH',rom,symbols['actor_dispatch']+i*8)
 assert actual==expected,(i,function,expected,actual)
 counts[function or 'fallback']=counts.get(function or 'fallback',0)+1
report=dict(passed=True,definitions=sum(counts.values()),routes=counts,rom_sha256=hashlib.sha256(rom).hexdigest(),scope='Every generated native frame callback and sprite layout/behavior route matches the existing family metadata. Pixel equivalence and gameplay have separate cartridge checks.')
(ROOT/'reports/actor-dispatch-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
