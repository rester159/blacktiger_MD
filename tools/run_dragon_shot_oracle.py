import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
for direction in range(16):
 for x in (-32,128,288):
  for wall,hit,full in ((0,0,0),(1,0,0),(0,1,0),(0,1,1)):
   cases.append(dict(kind=0,direction=direction,template=0x9dd6,root=s.word(3,0x9e26+direction*2)+5,x=x,y=96,wall=wall,hit=hit,full=full,left=direction>=8,profile=0))
for profile in (1,2):
 for left in (0,1):
  for wall,full in ((0,0),(1,0),(1,1)):
   cases.append(dict(kind=1,direction=0,template=0xa170,root=0xa1e4 if left else 0xa1a6,x=128,y=96,wall=wall,hit=0,full=full,left=left,profile=profile))
for x in (-32,128,288):cases.append(dict(kind=2,direction=0,template=0x9df6,root=0xa094,x=x,y=96,wall=0,hit=0,full=0,left=0,profile=0))
for c in cases:c['left']=int(c['left'])
t=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(t.index(0),t.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'dragon-shot-oracle',args);report['cases']=cases
(ROOT/'reference/dragon_shot_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
