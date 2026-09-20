import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
cases=[{'dx':dx,'dy':dy,'armor':a,'invincible':v} for dx in (-52,-51,-50,-24,0,24,50,51,52) for dy in (-25,-24,-23,0,23,24,25) for a,v in ((0,0),(4,100))]
lines,report=run_oracle(Source(),'hazard-oracle','return {'+','.join('{dx=%d,dy=%d,armor=%d,invincible=%d}'%(c['dx'],c['dy'],c['armor'],c['invincible']) for c in cases)+'}\n')
report['cases']=cases
(ROOT/'reports/hazard-oracle.json').write_text(json.dumps(report,indent=2)+'\n');print('observations',len(lines)-1)
