import json
from arcade_source import Source,ROOT
from extract_shop import extract
from oracle_runner import run_oracle
s=Source();data=extract(s);cases=[]
pcs=[0x6678,0x667c,0x6680,0x6684,0x66e0,0x66e4,0x66e8,0x66ec,0x674c,0x6787]
for d in range(8):
 for item,pc in enumerate(pcs,1):
  price=data['prices'][(item-1)//4][d][(item-1)%4] if item<=8 else data['key_price'] if item==9 else data['antidote_price']
  for money in (price-1,price,65535):
   cases.append(dict(item=item,pc=pc,difficulty=d,coins=money,weapon=0,armor=0,keys=0,antidotes=0,poison=0))
  c=dict(cases[-1]);c.update(weapon=4,armor=8,keys=99,antidotes=99);cases.append(c)
for poison in (1,2):
 c=dict(cases[-2]);c.update(poison=poison,antidotes=5);cases.append(c)
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(s,'shop-oracle',args);report['cases']=cases;report['default_difficulty']=int(lines[0].split('|')[1]);(ROOT/'reference/shop_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-2,report['default_difficulty'])
