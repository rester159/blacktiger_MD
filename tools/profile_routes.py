#!/usr/bin/env python3
"""Sample existing integration routes without changing their inputs or game state."""
import sys,json,struct,contextlib,io,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
import test_runtime as t
original=t.Runner.run;routes=[]
def run(self,n,mask=0):
 if n!=180:return original(self,n,mask)
 samples=[]
 for _ in range(n):
  original(self,1,mask);s=t.state(self)
  samples.append([s.frame,*struct.unpack('>3H',self.read('frame_cost',6)),*struct.unpack('>3H',self.read('video_cost',6)),int.from_bytes(self.read('video_dma_bytes'),'big'),sum(a.active>0 for a in s.actors)])
 routes.append({'round':s.round+1,'samples':samples})
t.Runner.run=run
with contextlib.redirect_stdout(io.StringIO()):t.test()
report={'rom_sha256':hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),'columns':['logic_frame','game','video','audio','background','sprites','overlay','dma_bytes','actors'],'routes':routes}
(ROOT/'reports/route-profile.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
for route in routes:
 values=route['samples'];print(route['round'],{name:round(sum(v[i] for v in values)/len(values),1) for i,name in enumerate(report['columns']) if i>0},'peak',max(v[2] for v in values))
