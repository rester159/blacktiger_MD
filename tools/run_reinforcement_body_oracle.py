import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
for profile,(template,root,score) in enumerate(((0x8899,0x8a49,0x20),(0xa07d,0xa22d,0x38),(0x947b,0x962b,0x28))):
 for px in (48,112,144,240):
  for random in range(0,32,2):
   for wall,damage,low in ((0,0,0),(96,255,0),(64,1,1)):
    cases.append(dict(profile=profile,template=template,root=root,score=score,px=px,py=96,y=96,vy=0,random=random,wall=wall,damage=damage,low=low,face=random%3==0,ticks=480,full=0))
cases += [dict(c,full=1) for c in cases if c['px']==112 and c['wall']==0]
for c in cases:c['face']=int(c['face'])
t=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(t.index(0),t.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'reinforcement-body-oracle',args);report['cases']=cases
(ROOT/'reference/reinforcement_body_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
