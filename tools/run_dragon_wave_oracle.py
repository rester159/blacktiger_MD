import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
for profile,base in enumerate((0xa397,0xa457)):
 for part in range(6):
  for left in (0,1):
   template=base+part*32
   cases.append(dict(profile=profile,part=part,template=template,root=s.word(3,template+30)+5,px=224,py=192,y=176,left=left,ticks=240))
args='return {cases={'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'dragon-wave-oracle',args);report['cases']=cases
(ROOT/'reference/dragon_wave_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
