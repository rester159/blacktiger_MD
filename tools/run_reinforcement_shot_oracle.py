import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(profile=p,template=base+48+i*32,part=i,x=x) for p,base in enumerate((0x8899,0xa07d)) for i in range(12) for x in (-32,128,288)]
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(s,'reinforcement-shot-oracle',args);report['cases']=cases
(ROOT/'reference/reinforcement_shot_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
