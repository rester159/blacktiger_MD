import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
for profile,template in enumerate((0x8045,0x9962,0x9b69)):
 for px in (48,128,208):
  for sample in range(16):
   for damage in (0,255):
    cases.append(dict(profile=profile,template=template,root=0x8369,score=0x70,px=px,py=120,y=96,face=0,vy=0,random=sample,damage=damage,ticks=1200,full=0))
cases += [dict(c,full=1) for c in cases if c['px']==128 and c['damage']==0]
cases += [dict(c,damage=1,ticks=480) for c in cases if c['px']==128 and c['damage']==0 and c['full']==0]
for c in cases:
 if c['profile']==2 and c['px']==128 and c['damage']==255 and c['random'] in (3,5,15):c['ticks']=1500
args='return {cases={'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'dragon-oracle',args);report['cases']=cases
(ROOT/'reference/dragon_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
