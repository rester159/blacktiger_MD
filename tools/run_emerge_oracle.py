import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
cases=[{'variant':v,'constructor':pc,'contact':contact,'damage':damage} for v,pc in enumerate((0x8000,0x81a2)) for contact,damage in ((False,False),(True,False),(False,True))]
lines,report=run_oracle(Source(),'emerge-oracle','return {'+','.join('{constructor=%d,contact=%s,damage=%s}'%(c['constructor'],str(c['contact']).lower(),str(c['damage']).lower()) for c in cases)+'}\n')
report['cases']=cases
(ROOT/'reports/emerge-oracle.json').write_text(json.dumps(report,indent=2)+'\n');print('observations',len(lines)-1)
