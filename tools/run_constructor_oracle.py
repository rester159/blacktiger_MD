#!/usr/bin/env python3
"""Trace real template copies for every current spawn constructor in original-ROM MAME."""
import os,subprocess,json,hashlib
from pathlib import Path
from arcade_source import Source,ROOT
s=Source();out=ROOT/'reports/constructor-oracle';out.mkdir(exist_ok=True)
romdir=out/'roms/blktiger';romdir.mkdir(parents=True,exist_ok=True)
for name in s.files:
 p=romdir/name
 if not p.exists():p.symlink_to((s.root/'payload'/name).resolve())
for name in ('cfg','nvram','sta','snap','diff','home'):(out/name).mkdir(exist_ok=True)
defs=json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions'];cases=[]
for d in defs:
 bank=d['bank'];blob=s.read(bank,0,0x8000)+s.read(bank,0x8000,0x4000)
 pcs=[i for i in range(len(blob)-1) if blob[i:i+2]==bytes.fromhex('edb0')]
 cases.append('{id=%d,bank=%d,pc=%d,copies={%s}}'%(d['id'],bank,d['address'],','.join(map(str,pcs))))
(out/'cases.lua').write_text('return {'+','.join(cases)+'}\n')
command=['/opt/homebrew/bin/mame','blktiger','-rompath',str(romdir.parent),'-debug','-debugger','none','-autoboot_delay','0','-autoboot_script',str(ROOT/'tools/constructor_oracle.lua'),'-video','none','-sound','none','-nothrottle','-skip_gameinfo','-noconfirm_quit','-noplugins','-nohttp','-nowriteconfig','-cfg_directory','cfg','-nvram_directory','nvram','-state_directory','sta','-snapshot_directory','snap','-diff_directory','diff','-homepath','home','-inipath','home']
run=subprocess.run(command,cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),capture_output=True,timeout=60)
(out/'stdout.txt').write_bytes(run.stdout);(out/'stderr.txt').write_bytes(run.stderr)
assert run.returncode==0,run.stderr.decode(errors='replace')
lines=(out/'events.txt').read_text().splitlines();assert lines[-1]=='COMPLETE',lines[-5:]
records=[]
for d in defs:
 copies=[];results=[];frames=[]
 for line in lines:
  v=line.split('|')
  if len(v)<2 or int(v[1])!=d['id']:continue
  if v[0]=='COPY':
   profile,pc,src,dest,ix=int(v[2]),int(v[3],16),int(v[4],16),int(v[5],16),int(v[6],16);raw=bytes.fromhex(v[7])
   assert s.read(d['bank'],src,len(raw))==raw
   copies.append({'profile':profile,'copy_pc':pc,'template_address':src,'destination':dest,'actor':ix,'bytes':v[7]})
  elif v[0]=='RESULT':results.append({'profile':int(v[2]),'persistence':v[3],'actors':v[4]})
  elif v[0]=='FRAME':frames.append({'profile':int(v[2]),'actor':int(v[3],16),'bytes':v[4],'display':v[5]})
 records.append({'frames':frames,'id':d['id'],'bank':d['bank'],'constructor':d['address'],'copies':copies,'results':results})
report={'oracle_sha256':hashlib.sha256((out/'events.txt').read_bytes()).hexdigest(),'lua_sha256':hashlib.sha256((ROOT/'tools/constructor_oracle.lua').read_bytes()).hexdigest(),'mame_sha256':hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),'source_set':s.lock['aggregate_sha256'],'scope':'Observed constructor copies under four controlled RAM profiles. Not a proof of all gameplay branches.','records':records}
(ROOT/'reference/constructor_oracle_events.txt').write_bytes((out/'events.txt').read_bytes())
(ROOT/'reference/constructors.json').write_text(json.dumps(report,indent=2)+'\n')
print('Constructors:',len(records),'with witnessed copies:',sum(bool(r['copies']) for r in records))
