import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(kind=kind,template=template,root=root,px=px,py=120,y=96,face=0,vy=0,random=sample,damage=damage,ticks=1000) for kind,template,root in ((0,0x9473,0x94a3),(1,0x8ec0,0x8ef0)) for px in (64,192) for sample in (0,3,7) for damage in (0,1,2,8,255)]
args='return {cases={'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'teleporter-oracle',args);report['cases']=cases;(ROOT/'reference/teleporter_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
