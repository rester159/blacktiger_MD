import json
from arcade_source import Source,ROOT
from extract_progress import extract
from oracle_runner import run_oracle
s=Source();data=extract(s);cases=[dict(maximum=i+1,score=t+offset) for i,t in enumerate(data['thresholds']) for offset in (-11,-10,-9,0,9000)]
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(s,'progress-oracle',args);report['cases']=cases;report['initial']=list(map(int,lines[0].split('|')[1:]));(ROOT/'reference/progress_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(report['initial'],len(cases))
