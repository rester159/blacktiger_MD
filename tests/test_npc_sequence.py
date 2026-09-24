"""Every native rescue update against independently captured source events."""
import ctypes as C,hashlib,json,re,subprocess,tempfile,struct,sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/npc_sequence_oracle.json').read_text())
for key,path in [('trace_sha256','reference/npc_sequence_oracle_events.txt'),('lua_sha256','tools/npc_sequence_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
meta=json.loads((ROOT/'reports/assets.json').read_text());defs={d['npc_kind']:d['id'] for d in meta['actor_definitions'] if d['npc_kind']}
rows=[l.split('|') for l in (ROOT/'reference/npc_sequence_oracle_events.txt').read_text().splitlines() if l!='COMPLETE']
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('');decl=(ROOT/'inc/assets.h').read_text();stubs=['#include "assets.h"','#include "npc.h"','Game game;u8 progress_max_hp=5;']
 for name in re.findall(r'^BIN (\w+)',(ROOT/'res/assets.res').read_text(),re.M):
  typ=re.search(r'extern const (\w+) '+name+r'\[\]',decl)[1];stubs.append('const '+typ+' '+name+'[1]={0};')
 stubs.append('''u8 terrain(s16 x,s16 y){return 0;}
 void setup(int def){game=(Game){0};game.mode=PLAY;game.coins=123;game.time=80;game.p.hp=1;game.p.invincible=2;game.actors[0]=(Actor){.def=def,.active=1};npc_reset();npc_spawn(0);npc_step(0,1);}
 void step(void){game.sound_count=0;npc_rescue_tick();}
 void snapshot(int *out){int v[]={npc_sequence.code,game.coins,game.time,game.p.hp,game.p.invincible,game.mode,npc_sequence.complete,game.sound_count};for(int i=0;i<8;i++)out[i]=v[i];}
 int sound_at(int i){return game.sound_commands[i];}
 ''');(tmp/'stub.c').write_text('\n'.join(stubs))
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),*[str(ROOT/'src'/s) for s in ('npc.c','animation.c','data.c')],str(tmp/'stub.c'),'-o',str(tmp/'npc.dylib')],check=True)
 lib=C.CDLL(str(tmp/'npc.dylib'));lib.npc_dialogue.restype=C.POINTER(C.c_ushort);count=0;sounds=0;used=set()
 for kind in range(1,9):
  events={}
  for tag,k,t,a,b in rows:
   if int(k)==kind:events.setdefault(int(t),[]).append((tag,int(a),int(b)))
  end=max(events);lib.setup(defs[kind]);cells=[32]*128;code=coins=0;coins=123;seconds=80;hp=1;invincible=2;mode=8;complete=0
  for tick in range(end+1):
   if tick:lib.step()
   commands=[]
   for tag,a,b in events.get(tick,[]):
    if tag=='TEXT':cells[a-256]=(cells[a-256]&0x700)|b
    elif tag=='ATTR':cells[a-256]=(cells[a-256]&255)|((b&224)<<3)
    elif tag=='SPRITE':code=a
    elif tag=='SOUND':commands.append(a)
    elif tag=='REWARD':
     if a==1:coins+=100
     elif a==3:hp=5;invincible=0
     elif a==4:seconds+=30
    elif tag=='END':mode=3 if a else 1;complete=1
   out=(C.c_int*8)();lib.snapshot(out)
   assert list(out)==[code,coins,seconds,hp,invincible,mode,complete,len(commands)],(kind,tick,list(out))
   assert list(lib.npc_dialogue()[:128])==cells,(kind,tick,'text')
   assert [lib.sound_at(i) for i in range(out[7])]==commands,(kind,tick,'sounds')
   used.update(cells);count+=1;sounds+=len(commands)
 sys.path.insert(0,str(ROOT/'tools'))
 from arcade_source import Source
 from extract import decode
 source=Source();board=json.loads((ROOT/'assets/board.json').read_text())
 chars=decode(b''.join(source.files[f['path']] for f in board['regions']['chars']['files']),board['layouts']['characters'])
 font=(ROOT/'res/generated/npc_dialogue_font.bin').read_bytes();glyphs=struct.unpack('>2048H',(ROOT/'res/generated/npc_dialogue_glyphs.bin').read_bytes())
 for code in used:
  tile=glyphs[code]&2047;slot=tile-1408 if tile>=1408 else tile-1072+32 if tile>=1072 else tile-1+48
  raw=np.frombuffer(font[slot*32:(slot+1)*32],dtype=np.uint8);pixels=np.column_stack((raw>>4,raw&15)).reshape(8,8)
  assert np.array_equal(pixels,np.array([1,15,6,0],dtype=np.uint8)[chars[code]]),('source glyph pixels',code)
 report=dict(passed=True,source_glyphs=len(used),variants=8,source_updates=count,sound_commands=sounds,scope='Every task-relative sprite code, text cell, reward, sound and terminal transition in all eight rescues. Source scheduler/task-list and HUD refresh bypasses remain explicit; glyph colors use native adaptation.')
 (ROOT/'reports/npc-sequence-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
