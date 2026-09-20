import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(template=0xba63,root=0xbafa,px=px,py=120,y=96,face=0,vy=0,random=sample,damage=damage,ticks=500) for px in (64,128,192) for sample in (0,1,8,15) for damage in (0,1,255)]
args='return {cases={'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'statue-oracle',args);report['cases']=cases;(ROOT/'reference/statue_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
