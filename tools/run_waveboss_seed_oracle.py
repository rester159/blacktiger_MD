import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(template=0x9b7f,root=0x9cb8 if left else 0x9c72,px=224,py=192,y=y,left=left,profile=profile,wall=wall,ticks=240) for left in (0,1) for profile in (0,1) for y in (80,144) for wall in (0,96)]
c=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(c.index(0),c.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in case.items())+'}' for case in cases)+'}}\n'
lines,report=run_oracle(s,'waveboss-seed-oracle',args);report['cases']=cases
(ROOT/'reference/waveboss_seed_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
