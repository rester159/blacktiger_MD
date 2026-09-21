import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
cases=[dict(command=c,phase=p) for c in (0x14,0x3c) for p in range(4)]
args='return {'+','.join('{command=%d,phase=%d}'%(c['command'],c['phase']) for c in cases)+'}\n'
lines,report=run_oracle(Source(),'sfx-long-oracle',args)
report.update(cases=cases,ends=[list(map(int,l.split('|')[1:])) for l in lines if l.startswith('END|')],scope='Full original long effects in all four envelope timer phases. Registers and private state sampled every 256 updates, each segment boundary and termination; scheduler isolated, no simultaneous-effect claim.')
(ROOT/'reference/sfx_long_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(report['ends'])
