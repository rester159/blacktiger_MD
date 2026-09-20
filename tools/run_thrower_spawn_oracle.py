import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();c=s.read(4,0xb63a,2048)
args='return {empty=%d,solid=%d,cases={{px=128,py=16,face=0,y=128,root=0x869e,vy=0,wall=0,ticks=1,hit_tick=0,hit2_tick=0}}}\n'%(c.index(0),c.index(3))
lines,report=run_oracle(s,'thrower-spawn-oracle',args)
(ROOT/'reference/thrower_spawn_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1,'observations')
