import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
cases=[]
for template,hp in ((0xa22b,16),(0xa28b,24)):
 for damage in ([hp,16],[100,100],[1,hp-2,1,1,14,1]):cases.append(dict(template=template,damage=damage))
args='return {'+','.join('{template=%d,damage={'%c['template']+','.join(map(str,c['damage']))+'}}' for c in cases)+'}\n'
lines,report=run_oracle(Source(),'boss-layers-oracle',args);report['cases']=cases
(ROOT/'reference/boss_layers_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1,'hits')
