from oracle_runner import mame_binary
#!/usr/bin/env python3
import os,subprocess,json,hashlib
from pathlib import Path
from arcade_source import Source,ROOT
from extract_hidden import extract
s=Source();d=extract(s);out=ROOT/'reports/hidden-oracle';out.mkdir(exist_ok=True)
romdir=out/'roms/blktiger';romdir.mkdir(parents=True,exist_ok=True)
for name in s.files:
 p=romdir/name
 if not p.exists():p.symlink_to((s.root/'payload'/name).resolve())
for name in ('cfg','nvram','sta','snap','diff','home'):(out/name).mkdir(exist_ok=True)
cases=['{round=%d,persistent=%d,bank=%d,address=%d}'%(r,p['persistent'],p['bank'],p['address']) for r,patches in enumerate(d['rounds']) for p in patches]
(out/'cases.lua').write_text('return {'+','.join(cases)+'}\n')
command=[mame_binary(),'blktiger','-rompath',str(romdir.parent),'-debug','-debugger','none','-autoboot_delay','0','-autoboot_script',str(ROOT/'tools/hidden_oracle.lua'),'-video','none','-sound','none','-nothrottle','-skip_gameinfo','-noconfirm_quit','-noplugins','-nohttp','-nowriteconfig','-cfg_directory','cfg','-nvram_directory','nvram','-state_directory','sta','-snapshot_directory','snap','-diff_directory','diff','-homepath','home','-inipath','home']
run=subprocess.run(command,cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),capture_output=True,timeout=60)
(out/'stdout.txt').write_bytes(run.stdout);(out/'stderr.txt').write_bytes(run.stderr);assert run.returncode==0
lines=(out/'events.txt').read_text().splitlines();assert lines[-1]=='COMPLETE'
count=0
for line in lines:
 v=line.split('|')
 if v[0]=='PATCH':assert v[3:]==['0030','0030','03'],v;count+=1
 elif v[0]=='REWARD':
  k=int(v[1]);life,armor,hp=int(v[2],16),int(v[3],16),int(v[4],16)
  coins=int.from_bytes(bytes.fromhex(v[5]),'little');timer=int.from_bytes(bytes.fromhex(v[6]),'little')
  assert life==(4 if k==1 else 3),(k,'life',v)
  assert armor==({2:4,6:4,7:5}.get(k,2)),(k,'armor',v)
  assert hp==(4 if k==2 else 1),(k,'hp',v)
  assert coins==({5:1123,10:623}.get(k,123)),(k,'coins',v)
  assert timer==(0x230 if k==4 else 0x200),(k,'time',v)
  if k in (8,9,11):assert {8:'0570',9:'0590',11:'0598'}[k] in [v[7][i:i+4] for i in range(0,len(v[7]),4)],v
assert count==39
(ROOT/'reference/hidden_oracle_events.txt').write_bytes((out/'events.txt').read_bytes())
report={'passed':True,'patch_cases':count,'reward_cases':12,'source_set':s.lock['aggregate_sha256'],'trace_sha256':hashlib.sha256((out/'events.txt').read_bytes()).hexdigest(),'lua_sha256':hashlib.sha256((ROOT/'tools/hidden_oracle.lua').read_bytes()).hexdigest(),'scope':'Original break damage/callback writes for 39 patches; reveal and reward dispatch for 12 kinds. Player contact geometry and screen-attack enemy coverage are separate.'}
(ROOT/'reports/hidden-oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
