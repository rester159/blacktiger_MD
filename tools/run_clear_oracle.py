import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[dict(kind=0,round=r,weapon=w,armor=a) for r in (0,7) for w in range(5) for a in (0,2)]
cases += [dict(kind=1,round=r,weapon=0,armor=2,coins=v) for r in range(8) for v in (0,200,65000,65535)]
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(s,'clear-oracle',args);report.update(cases=cases,scope='Victory sprite writes and task-relative waits after grounded entry; protection loops and scheduler dispatch skipped. Separate payout body includes all eight table rows, but final-round control flow bypasses it.')
report['durations']=[list(map(int,l.split('|')[1:])) for l in lines if l.startswith('END|')]
(ROOT/'reference/clear_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['durations']))
