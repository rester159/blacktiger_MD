#!/usr/bin/env python3
"""Package only the exact cartridge that passed the recorded tests."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rom=ROOT/'out/release/rom.bin';raw=rom.read_bytes();assert raw[0x100:0x104]==b'SEGA'
checksum=sum(int.from_bytes(raw[i:i+2],'big') for i in range(0x200,len(raw),2))&65535
assert int.from_bytes(raw[0x18e:0x190],'big')==checksum
assert int.from_bytes(raw[0x1a4:0x1a8],'big')==len(raw)-1
source=ROOT.parent/'_capcom/black tiger/assets/source_packages/arcade/blktiger_supplied_romset_e54221c17ce6b5ee/payload'
checked=0
if source.exists():
 for name in ('bdu-01a.5e','bdu-02a.6e','bdu-03a.8e'):
  b=(source/name).read_bytes()
  for at in range(0,len(b)-255,256):
   part=b[at:at+256]
   if len(set(part))<32:continue
   assert part not in raw,(name,hex(at));checked+=1
assets=json.loads((ROOT/'reports/asset-tests.json').read_text());tests=json.loads((ROOT/'reports/runtime-tests.json').read_text());assert tests['rom_sha256']==sha(rom)
npc=json.loads((ROOT/'reports/npc-runtime-tests.json').read_text());assert npc['passed'] and npc['rom_sha256']==sha(rom)
anim=json.loads((ROOT/'reports/animation-tests.json').read_text());assert anim['passed']
actors=json.loads((ROOT/'reports/actor-contract-tests.json').read_text());assert actors['passed'] and actors['rom_sha256']==sha(rom)
report={'actor_initial_state_checks':actors,'npc_variants_passed':len(npc['variants']),'source_animation_trace_comparisons':anim['original_trace_comparisons'],'status':'development prototype; complete port not achieved','rom':'blacktiger_astra.bin','rom_bytes':len(raw),'rom_sha256':sha(rom),'checksum':checksum,'asset_checks_passed':assets['passed'],'runtime_checks_passed':tests['passed'],'full_rate_all_routes':tests['full_rate_all_routes'],'cadence':tests['cadence'],'arcade_program_chunk_audit':{'chunks_checked':checked,'embedded_matches':0,'limitation':'Supporting check, not a formal proof of the entire runtime call graph.'},'native_sources':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'src').glob('*.c'))},'build_command':'make test && python3 tools/package.py','limitations':['Unverified and provisional actor/boss behaviors and graphics mappings','Original music missing; native PSG placeholder effects','No full natural playthrough or real-hardware validation','NTSC cadence shortfalls; PAL unverified']}
out=ROOT/'dist';out.mkdir(exist_ok=True);shutil.copyfile(rom,out/'blacktiger_astra.bin');shutil.copyfile(ROOT/'out/release/symbol.txt',out/'symbols.txt');(out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('rom_bytes','rom_sha256','asset_checks_passed','runtime_checks_passed','full_rate_all_routes')}))
