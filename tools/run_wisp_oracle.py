import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
cases=[{'random':r,'y':y,'switch':switch,'hit':hit} for r in (0,1) for y,switch,hit in ((96,False,False),(220,False,False),(220,True,False),(96,False,True))]
lines,report=run_oracle(Source(),'wisp-oracle','return {'+','.join('{random=%d,y=%d,switch=%s,hit=%s}'%(c['random'],c['y'],str(c['switch']).lower(),str(c['hit']).lower()) for c in cases)+'}\n')
report['cases']=cases
(ROOT/'reports/wisp-oracle.json').write_text(json.dumps(report,indent=2)+'\n');print('observations',len(lines)-1)
