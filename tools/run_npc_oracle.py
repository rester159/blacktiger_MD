from oracle_runner import mame_binary
#!/usr/bin/env python3
"""Execute a bounded original-ROM oracle and verify independently decoded data."""
import os,subprocess,json,hashlib
from pathlib import Path
from arcade_source import Source,ROOT
from extract_animation import extract
source=Source();contract=extract(source);out=ROOT/'reports/npc-oracle';out.mkdir(exist_ok=True)
romdir=out/'roms/blktiger';romdir.mkdir(parents=True,exist_ok=True)
for name in source.files:
 p=romdir/name
 if not p.exists():p.symlink_to((source.root/'payload'/name).resolve())
for name in ('cfg','nvram','sta','snap','diff','home'):(out/name).mkdir(exist_ok=True)
command=[mame_binary(),'blktiger','-rompath',str(romdir.parent),'-debug','-debugger','none','-autoboot_delay','0','-autoboot_script',str(ROOT/'tools/npc_oracle.lua'),'-video','none','-sound','none','-nothrottle','-skip_gameinfo','-noconfirm_quit','-noplugins','-nohttp','-nowriteconfig','-cfg_directory','cfg','-nvram_directory','nvram','-state_directory','sta','-snapshot_directory','snap','-diff_directory','diff','-homepath','home','-inipath','home']
run=subprocess.run(command,cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),capture_output=True,timeout=60)
(out/'stdout.txt').write_bytes(run.stdout);(out/'stderr.txt').write_bytes(run.stderr)
assert run.returncode==0,run.stderr.decode(errors='replace')
lines=(out/'events.txt').read_text().splitlines();assert lines[-1]=='COMPLETE';counts={};failures=[]
for line in lines:
 v=line.split('|');counts[v[0]]=counts.get(v[0],0)+1
 if v[0]=='NPC':
  k=int(v[1]);actual=bytes.fromhex(v[2]);expected=bytearray.fromhex(contract['npc']['template']);expected[1:5]=b'\x00\x80\x00\x80';expected[11]=33+k;expected[13]=44+k;expected[24:28]=bytes.fromhex('58ecfeac')
  assert actual==expected,(k,actual.hex(),expected.hex())
  assert v[3]==('01080000' if k==7 else '01000000')
 elif v[0]=='IDLE':
  tick=int(v[1]);a=bytes.fromhex(v[2]);assert a[10]==200-(tick-1)%200 and a[30:32]==bytes.fromhex('615f')
  assert v[3]=='00648080016480900864908009649090',v
 elif v[0]=='FRAME':
  entry=int(v[1],16);tick=int(v[2]);a=bytes.fromhex(v[3]);phase=(tick-1)%6
  # Independent handwritten fixture expectation, including velocity retention.
  x=80+sum(1 if (j%6)<5 else -1 for j in range(tick));y=80+tick*2
  assert int.from_bytes(a[1:3],'big')==x and int.from_bytes(a[3:5],'big')==y,(tick,a.hex())
  assert a[6:8]==(bytes([255,2]) if phase==5 else bytes([1,2]))
  assert a[10]==(2-phase if phase<2 else 5-phase if phase<5 else 1)
 elif v[0]=='COINS':assert int.from_bytes(bytes.fromhex(v[1]),'little')==223
 elif v[0]=='HEAL':assert v[1:] == ['07','00']
 elif v[0]=='TIME':
  sec=int(v[1])+30;raw=bytes.fromhex(v[2]);assert raw==bytes([(sec%60//10)*16+sec%10,2+sec//60]),v
assert counts['NPC']==8 and counts['FRAME']==28 and counts['TIME']==60
report={'passed':True,'counts':counts,'source_set':source.lock['aggregate_sha256'],'mame_sha256':hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),'lua_sha256':hashlib.sha256((ROOT/'tools/npc_oracle.lua').read_bytes()).hexdigest(),'event_sha256':hashlib.sha256((out/'events.txt').read_bytes()).hexdigest(),'scope':'All eight NPC constructor states; 402 idle animation ticks; common small/medium frame-loader velocity and loop semantics; coin/heal/time reward writes. Does not prove rescue cutscene timing or shop logic.'}
(ROOT/'reports/npc-oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
