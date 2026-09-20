import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(template=template,root=s.word(0,template+30)+5,px=px,py=py,y=96,face=0,vy=0,random=0,wall=wall,damage=damage,ticks=400,score=score) for template,score in ((0xaea6,0x20),(0xaed6,0x20),(0xb534,0x30),(0xb564,0x30)) for px,py in ((48,96),(128,96),(208,96),(128,120)) for wall in (0,96,64) for damage in (0,1,255)]
c=s.read(4,0xb63a,2048);args='return {empty=%d,solid=%d,cases={'%(c.index(0),c.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in case.items())+'}' for case in cases)+'}}\n'
lines,report=run_oracle(s,'flailer-oracle',args);report['cases']=cases;(ROOT/'reference/flailer_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
