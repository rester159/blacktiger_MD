import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(template=0x9473,root=0x94a3,px=px,py=120,y=96,face=0,vy=0,random=sample,damage=damage,ticks=1000) for px in (64,192) for sample in (0,3,7) for damage in (0,1,2,8,255)]
args='return {cases={'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'teleporter-oracle',args);report['cases']=cases;(ROOT/'reference/teleporter_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
