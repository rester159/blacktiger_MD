import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(template=template,root=0xa309,px=px,py=120,y=96,face=0,vy=0,random=sample,damage=damage,ticks=300) for template in (0xa259,0xa289) for px in (48,128,208) for sample in range(16) for damage in (0,255)]
args='return {cases={'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'hunter-oracle',args);report['cases']=cases;(ROOT/'reference/hunter_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
