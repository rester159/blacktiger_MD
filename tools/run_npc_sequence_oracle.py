import json
from arcade_source import Source, ROOT
from oracle_runner import run_oracle
lines, report = run_oracle(Source(), 'npc-sequence-oracle')
(ROOT/'reference/npc_sequence_oracle.json').write_text(json.dumps(report, indent=2)+'\n')
print(len(lines))
