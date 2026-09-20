import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
lines,report=run_oracle(Source(),'pickup-oracle')
report['observations']=len(lines)-1
(ROOT/'reports/pickup-oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(report['observations'])
