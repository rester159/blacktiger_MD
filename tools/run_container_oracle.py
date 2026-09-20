import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
cases=[dict(round=r,seed=seed) for r in range(8) for seed in (0,1,2,255,256,451,1024,4095,32767,32768,65535,0x1234,0x8765,0xabcd,0xaaaa,0x5555)]
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(Source(),'container-oracle',args);report['cases']=cases
(ROOT/'reference/container_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
