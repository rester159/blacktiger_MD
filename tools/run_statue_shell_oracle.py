import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(template=0xba93,root=s.word(0,0xbbc4+angle*2)+5,px=160,py=120,y=96,hit_tick=hit,contact_tick=contact,damage=1,ticks=180) for angle in range(16) for hit,contact in ((0,0),(3,0),(0,3))]
args='return {cases={'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'statue-shell-oracle',args);report['cases']=cases;(ROOT/'reference/statue_shell_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
