import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(template=0xa2b9,root=s.word(1,0xaa84+angle*2)+5,px=160,py=120,y=96,mode=mode,wall=wall,hit_tick=hit,contact_tick=contact,damage=1,ticks=100) for angle in range(16) for mode,wall,hit,contact in ((8,0,0,0),(8,96,0,0),(8,0,3,0),(8,0,0,3),(9,0,3,0))]
c=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={'%(c.index(0),c.index(3))+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'hunter-shell-oracle',args);report['cases']=cases;(ROOT/'reference/hunter_shell_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
