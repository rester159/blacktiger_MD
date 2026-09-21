import json,gzip
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
lines,report=run_oracle(Source(),'intro-oracle')
(ROOT/'reference/intro_oracle.json').write_text(json.dumps(report,indent=2)+'\n')
p=ROOT/'reference/intro_oracle_events.txt'
p.with_suffix('.txt.gz').write_bytes(gzip.compress(p.read_bytes(),mtime=0));p.unlink()
print(len(lines))
