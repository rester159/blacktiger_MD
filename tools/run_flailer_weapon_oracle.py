import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(template=0xaf06+profile*0x68e,root=(0xb0b8 if left else 0xb0f0)+profile*0x68e,px=224,py=192,y=96,left=left,profile=profile,hit_tick=hit,cancel_tick=cancel,damage=1,ticks=180) for profile in (0,1) for left in (0,1) for hit,cancel in ((0,0),(3,0),(30,0),(0,3),(0,30))]
args='return {cases={'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}}\n'
lines,report=run_oracle(s,'flailer-weapon-oracle',args);report['cases']=cases;(ROOT/'reference/flailer_weapon_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
