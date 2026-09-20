import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(invincible=invincible,poison_contact=kind,poison=poison,gate=gate,reverse=reverse,antidotes=antidotes) for invincible in (0,1) for kind in (0,1,2) for poison in (0,38) for gate in (0,1,30,60) for reverse in (0,1) for antidotes in (0,1,99)]
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(s,'status-oracle',args);report['cases']=cases
s.expect(7,0xa0b9,'3a15e9473a2fe0b0c29fa1');report['poison_dagger_gate']=True
report['control_tables']=[list(s.read(7,pc,32)) for pc in (0x90a6,0x90c6)]
(ROOT/'reference/status_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
