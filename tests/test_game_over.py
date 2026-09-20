"""Source-witnessed game-over timing and native free-play continue lifecycle."""
import ctypes as C,json,subprocess,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from arcade_source import Source
s=Source()
for pc,raw in [(0x20b0,'3e07cd3e03'),(0x033e,'f5cd2003f13d20f8c9'),(0x0320,'3e3c'),(0x20db,'3e34cde203'),(0x20ec,'2188b8060a'),(0x20fd,'0619c5'),(0x2160,'cd0803c11099c1e105c2f120'),(0x0308,'3e03'),(0x2118,'3a25e032a0f3'),(0x2124,'21e8e111e9e10107003600edb0')]:s.expect(None,pc,raw)
with tempfile.TemporaryDirectory() as folder:
 p=Path(folder);(p/'stub.c').write_text('#include "game_over.h"\n#include "music.h"\nu8 music_request;\nint phase(void){return game_over.phase;}int digit(void){return game_over.digit;}')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),str(ROOT/'src/game_over.c'),str(p/'stub.c'),'-o',str(p/'over.dylib')],check=True)
 lib=C.CDLL(str(p/'over.dylib'));lib.game_over_start()
 for i in range(420):assert lib.game_over_step(64)==0
 assert lib.phase()==2 and C.c_uint8.in_dll(lib,'music_request').value==0x34
 seen=[]
 for tick in range(750):
  seen.append(lib.digit());assert lib.game_over_step(0)==(2 if tick==749 else 0)
 assert seen==[digit for digit in range(9,-1,-1) for _ in range(75)]
 for delay in (0,1,2,3,74,75,747,748):
  lib.game_over_start()
  for _ in range(420+delay):assert lib.game_over_step(0)==0
  for wait in range(3):
   result=lib.game_over_step(64)
   if result:break
  assert result==(2 if delay==748 else 1),(delay,result)
 lib.game_over_reset();assert lib.phase()==0
report=dict(passed=True,notice_updates=420,offer_updates=750,digit_updates=75,input_poll_updates=3,accept_cases=7,last_poll_expiry=True,console_adaptation='Free continues with Start; no arcade credit input.',source_set=s.lock['aggregate_sha256'],witnesses=list(s.witnesses.values()))
(ROOT/'reports/game-over-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
