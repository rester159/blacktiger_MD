import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
lines,report=run_oracle(Source(),'weapon-oracle')
(ROOT/'reference/weapon_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(lines)
