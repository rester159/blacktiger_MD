import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
commands=[*range(1,31),*range(0x3a,0x40)]
cases=[dict(command=c,phase=p) for c in commands for p in range(4)]
args='return {'+','.join('{command=%d,phase=%d}'%(c['command'],c['phase']) for c in cases)+'}\n'
lines,report=run_oracle(Source(),'sfx-oracle',args)
report.update(cases=cases,writes=sum(l.startswith('WRITE|') for l in lines),scope='Original isolated SSG register writes, termination/periodic state, all 36 effects at all four software-envelope timer phases. No simultaneous-effect/whole-board schedule claim.')
(ROOT/'reference/sfx_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(report['writes'])
