"""Run isolated development-only original-ROM observations."""
import os,subprocess,hashlib
from arcade_source import ROOT
from pathlib import Path

def run_oracle(source,name,cases='return {}\n'):
 out=ROOT/'reports'/name;out.mkdir(exist_ok=True)
 romdir=out/'roms/blktiger';romdir.mkdir(parents=True,exist_ok=True)
 for filename in source.files:
  p=romdir/filename
  if not p.exists():p.symlink_to((source.root/'payload'/filename).resolve())
 for folder in ('cfg','nvram','sta','snap','diff','home'):(out/folder).mkdir(exist_ok=True)
 (out/'cases.lua').write_text(cases)
 script=ROOT/'tools'/(name.replace('-','_')+'.lua')
 command=['/opt/homebrew/bin/mame','blktiger','-rompath',str(romdir.parent),'-debug','-debugger','none','-autoboot_delay','0','-autoboot_script',str(script),'-video','none','-sound','none','-nothrottle','-skip_gameinfo','-noconfirm_quit','-noplugins','-nohttp','-nowriteconfig','-cfg_directory','cfg','-nvram_directory','nvram','-state_directory','sta','-snapshot_directory','snap','-diff_directory','diff','-homepath','home','-inipath','home']
 try:
  run=subprocess.run(command,cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),capture_output=True,timeout=60)
 except subprocess.TimeoutExpired as error:
  (out/'stdout.txt').write_bytes(error.stdout or b'');(out/'stderr.txt').write_bytes(error.stderr or b'');raise
 (out/'stdout.txt').write_bytes(run.stdout);(out/'stderr.txt').write_bytes(run.stderr)
 assert run.returncode==0,run.stderr.decode(errors='replace')
 raw=(out/'events.txt').read_bytes();lines=raw.decode().splitlines();assert lines[-1]=='COMPLETE',lines[-4:]
 (ROOT/'reference'/(name.replace('-','_')+'_events.txt')).write_bytes(raw)
 return lines,{'source_set':source.lock['aggregate_sha256'],'trace_sha256':hashlib.sha256(raw).hexdigest(),'lua_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'mame_sha256':hashlib.sha256(Path(command[0]).read_bytes()).hexdigest()}
