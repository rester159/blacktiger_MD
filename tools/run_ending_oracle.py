import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
lines,report=run_oracle(Source(),'ending-oracle')
report.update(ticks=int(next(l for l in lines if l.startswith('END|')).split('|')[1]),scope='Original ending text writes, clear requests, palette steps, credits map and task-relative waits through 2013. Inherited palettes initialized from source; actor deletion and task scheduling bypassed. No whole-board timing or sprite-retention claim.')
(ROOT/'reference/ending_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
