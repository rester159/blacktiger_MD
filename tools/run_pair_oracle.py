import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
for part,template,root in [(0,0xadc9,0xae09),(1,0xade9,0xaeff)]:
 for sample in range(16):
  cases.append(dict(part=part,template=template,root=root,px=32 if sample&1 else 224,py=16 if sample&2 else 192,y=96,random=sample,ticks=1800,hit_tick=0,damage=0))
 cases.append(dict(part=part,template=template,root=root,px=224,py=192,y=96,random=3,ticks=200,hit_tick=150,damage=1))
args='return {cases={'+','.join('{'+','.join(f'{k}={v}' for k,v in case.items())+'}' for case in cases)+'}}\n'
lines,report=run_oracle(s,'pair-oracle',args);report['cases']=cases
(ROOT/'reference/pair_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1,'source ticks')
