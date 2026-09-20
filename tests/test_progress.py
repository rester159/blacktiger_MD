#!/usr/bin/env python3
import ctypes as C,json,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'reference/progress_oracle.json').read_text());data=json.loads((ROOT/'reference/progress.json').read_text())
for key,path in [('trace_sha256','reference/progress_oracle_events.txt'),('lua_sha256','tools/progress_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder);(tmp/'genesis.h').write_text('')
 (tmp/'stub.c').write_text('#include "assets.h"\n#include "progress.h"\nGame game;\nconst u8 progress_initial_health=1;\nconst u32 progress_thresholds[4]={'+','.join(map(str,data['thresholds']))+'};\nvoid setup(int score,int maximum){game.score=score;game.p.hp=1;progress_max_hp=maximum;}\nint score(void){return game.score;}\nint hp(void){return game.p.hp;}\n')
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(tmp),'-I'+str(ROOT/'inc'),str(ROOT/'src/progress.c'),str(tmp/'stub.c'),'-o',str(tmp/'p.dylib')],check=True)
 lib=C.CDLL(str(tmp/'p.dylib'));maximum=C.c_uint8.in_dll(lib,'progress_max_hp');count=0
 for line in (ROOT/'reference/progress_oracle_events.txt').read_text().splitlines():
  if not line.startswith('SCORE|'):continue
  _,case,score,cap,hp=line.split('|');c=ref['cases'][int(case)];lib.setup(c['score'],c['maximum']);lib.progress_score(10)
  assert (lib.score(),maximum.value,lib.hp())==tuple(map(int,(score,cap,hp))),(c,score,cap,hp)
  count+=1
 assert ref['initial']==[data['initial_lives'],data['initial_health'],data['initial_health'],data['initial_coins'],data['initial_armor'],0]
 report={'passed':True,'source_score_cases':count,'initial_resources':ref['initial'],'thresholds':data['thresholds'],'scope':'Source initialization slices (RAM clear, DIP lives, player copy, initial resource grant) and original score task across every ordinary vitality threshold. One increase per award and no automatic healing. Full boot scheduling, continue/death equipment resets and maximum-score saturation remain separate.'}
 (ROOT/'reports/progress-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
