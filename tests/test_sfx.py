"""Native SSG stream fidelity, source priorities, PSG bounds and regional timing."""
import ctypes as C,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];meta=json.loads((ROOT/'reference/sfx.json').read_text());ref=json.loads((ROOT/'reference/sfx_oracle.json').read_text())
for k,p in [('trace_sha256','reference/sfx_oracle_events.txt'),('lua_sha256','tools/sfx_oracle.lua')]:assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==ref[k]
cases=[]
for l in (ROOT/'reference/sfx_oracle_events.txt').read_text().splitlines():
 f=l.split('|')
 if f[0]=='CASE':c=dict(command=int(f[1]),phase=int(f[2]),writes=[]);cases.append(c)
 elif f[0] in ('END','BOUNDED'):c.update(kind=f[0],end=int(f[1]))
 elif f[0]=='WRITE':c['writes'].append(tuple(map(int,f[1:])))
class Slot(C.Structure):_fields_=[('track',C.c_void_p),('position',C.c_uint16),('tick',C.c_uint16),('command',C.c_uint8),('active',C.c_uint8),('regs',C.c_uint8*11)]
with tempfile.TemporaryDirectory() as directory:
 tmp=Path(directory);(tmp/'stub.c').write_text('#include "sfx.h"\nu16 tones[3];u8 volumes[4],noise;\nvoid sfx_tone(u8 c,u16 p){tones[c]=p;}void sfx_volume(u8 c,u8 v){volumes[c]=v;}void sfx_noise(u8 n){noise=n;}\n')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/sfx.c'),str(tmp/'stub.c'),'-o',str(tmp/'sfx.dylib')],check=True)
 lib=C.CDLL(str(tmp/'sfx.dylib'));slots=(Slot*2).in_dll(lib,'sfx_slots');phase=C.c_uint8.in_dll(lib,'sfx_phase');ticks=C.c_uint32.in_dll(lib,'sfx_ticks');volumes=(C.c_uint8*4).in_dll(lib,'volumes');tones=(C.c_uint16*3).in_dll(lib,'tones');count=0;profiles=0
 for c in cases:
  if c['kind']!='END':continue
  for pal in (0,1):
   lib.sfx_reset();phase.value=c['phase'];assert lib.sfx_start(c['command']);slot=c['writes'][0][1];expected=bytearray(11);at=0;fraction=0;clock=0
   while True:
    s=slots[slot]
    while at<len(c['writes']) and c['writes'][at][0]<=s.tick:
     _,chip,reg,value=c['writes'][at];expected[reg]=value;at+=1
    assert bytes(s.regs)==expected,(c['command'],c['phase'],pal,s.tick,'registers')
    assert s.active==(s.tick<c['end'])
    lib.sfx_render(pal);assert all(0<=v<=15 for v in volumes);assert all(1<=v<=1023 for v in tones) if s.active else list(volumes)==[15]*4
    count+=1
    if not s.active:break
    n=1+(count%3);lib.sfx_advance(n,pal);fraction+=n*(308939 if pal else 7467);den=61461 if pal else 1791;clock+=fraction//den;fraction%=den
    assert ticks.value==clock and phase.value==(c['phase']+clock)%4
   assert at==len(c['writes']);profiles+=1
 # A known three-tone chord and shared-noise clock exercise the hardware adaptation.
 lib.sfx_reset();lib.sfx_start(0x1b);slots[0].regs[:]=[100,0,200,0,44,1,16,56,15,14,13]
 lib.sfx_render(0);assert list(tones)==[100,200,300] and list(volumes)==[meta['attenuation'][v] for v in [15,14,13]]+[15]
 slots[0].regs[7]=48;lib.sfx_render(0);assert C.c_uint8.in_dll(lib,'noise').value==4 and list(tones)==[100,200,300]
 slots[0].regs[6]=7;lib.sfx_render(0);assert C.c_uint8.in_dll(lib,'noise').value==7 and list(tones)==[100,200,7] and volumes[2]==15
 lib.sfx_render(1);assert list(tones)==[99,198,7]
 # Higher/equal source slot priority replaces; lower does not. Other slot survives.
 lib.sfx_reset();assert lib.sfx_start(1);assert not lib.sfx_start(0x1b);assert slots[0].command==1
 assert lib.sfx_start(2) and slots[0].command==2
 assert lib.sfx_start(3) and slots[1].active and slots[0].active
 assert not lib.sfx_start(0x14) and not lib.sfx_start(0x3c)
 lib.sfx_render(0);assert all(1<=v<=1023 for v in tones)
 assert lib.sfx_start(0x1f) and not any(s.active for s in slots);lib.sfx_render(0);assert list(volumes)==[15]*4
report=dict(passed=True,profiles_regions=profiles,register_state_batches=count,priority_replacement=True,two_slots=True,stop=True,unsupported_rejected=meta['unsupported'],scope='All 136 finite command/timer-phase profiles at both regional accumulators against original register writes through completion; priority and stop checks; PSG register bounds. Timbre/noise mixing are adaptations, not waveform equivalence.')
(ROOT/'reports/sfx-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
