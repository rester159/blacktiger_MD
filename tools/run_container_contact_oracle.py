import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
from extract_container import extract
s=Source();data=extract(s)
cases=[dict(content=i,pc=pc,keys=keys,opened=opened,collected=0,coins=coins,hp=hp,max_hp=maximum,invincible=inv) for i,pc in enumerate(data['contact_handlers']) for keys in (0,1,9,99) for opened in (0,1) for coins,hp,maximum,inv in ((0,1,4,1),(65500,3,8,0),(999,4,4,255))]
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(s,'container-contact-oracle',args);report['cases']=cases
(ROOT/'reference/container_contact_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
