from oracle_runner import mame_binary
#!/usr/bin/env python3
import os,subprocess,json,hashlib
from pathlib import Path
from arcade_source import Source,ROOT
from extract_skeleton import extract,ROOTS,CONSTRUCTORS
s=Source();d=extract(s);out=ROOT/'reports/skeleton-oracle';out.mkdir(exist_ok=True)
romdir=out/'roms/blktiger';romdir.mkdir(parents=True,exist_ok=True)
for name in s.files:
 p=romdir/name
 if not p.exists():p.symlink_to((s.root/'payload'/name).resolve())
for name in ('cfg','nvram','sta','snap','diff','home'):(out/name).mkdir(exist_ok=True)
base=[('walk_left',0,64,16,128,0,0,40),('walk_right',0,192,16,128,0,0,40),('combat_left',0,80,128,128,0,0,150),('combat_right',0,176,128,128,0,0,150),('fall',13,220,300,80,0,0,40),('jump',9,220,80,128,-4,0,50),('low_wall',3,240,128,128,0,144,70),('high_wall',3,240,128,128,0,96,70),('damage',0,220,16,128,0,0,60),('guard',0,220,16,128,0,0,60)]
cases=[]
for variant in range(3):
 for name,root,px,py,y,vy,wall,ticks in base:
  c=dict(name=name,variant=variant,root_index=root,root=ROOTS[variant][root],constructor=CONSTRUCTORS[variant],px=px,py=py,y=y,vy=vy,wall=wall,ticks=ticks,face=int(name=='guard'),hit_tick=0,damage=0,hit2_tick=0,damage2=0)
  if name=='damage':c.update(hit_tick=8,damage=5,hit2_tick=20,damage2=100)
  if name=='guard':c.update(hit_tick=2,damage=d['profiles'][variant]['durability']+d['profiles'][variant]['guard'],hit2_tick=20,damage2=d['profiles'][variant]['guard']+1)
  cases.append(c)
collision=s.read(4,0xb63a,2048);empty=collision.index(0);solid=collision.index(3)
lua_cases=['{'+','.join(f'{k}={v}' for k,v in c.items() if isinstance(v,int))+'}' for c in cases]
(out/'cases.lua').write_text('return {empty=%d,solid=%d,cases={'%(empty,solid)+','.join(lua_cases)+'}}\n')
command=[mame_binary(),'blktiger','-rompath',str(romdir.parent),'-debug','-debugger','none','-autoboot_delay','0','-autoboot_script',str(ROOT/'tools/skeleton_oracle.lua'),'-video','none','-sound','none','-nothrottle','-skip_gameinfo','-noconfirm_quit','-noplugins','-nohttp','-nowriteconfig','-cfg_directory','cfg','-nvram_directory','nvram','-state_directory','sta','-snapshot_directory','snap','-diff_directory','diff','-homepath','home','-inipath','home']
run=subprocess.run(command,cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),capture_output=True,timeout=60)
(out/'stdout.txt').write_bytes(run.stdout);(out/'stderr.txt').write_bytes(run.stderr);assert run.returncode==0
lines=(out/'events.txt').read_text().splitlines();assert lines[-1]=='COMPLETE'
assert len(lines)-1==sum(c['ticks'] for c in cases)
(ROOT/'reference/skeleton_oracle_events.txt').write_bytes((out/'events.txt').read_bytes())
report={'source_set':s.lock['aggregate_sha256'],'cases':cases,'ticks':len(lines)-1,'trace_sha256':hashlib.sha256((out/'events.txt').read_bytes()).hexdigest(),'lua_sha256':hashlib.sha256((ROOT/'tools/skeleton_oracle.lua').read_bytes()).hexdigest(),'scope':'Three original skeleton variants: walking, attack cycles, weapon actors, falling, jumping, obstacles, damage and directional blocks on controlled terrain.'}
(ROOT/'reference/skeleton_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print('Original trace:',len(cases),'cases,',report['ticks'],'ticks')
