import json
from arcade_source import Source,ROOT
from extract_checkpoint import extract
from oracle_runner import run_oracle
s=Source();data=extract(s);cases=[]
for r,wide in enumerate(data['wide']):
 columns=8 if wide else 4
 for cell in range(32):
  for dx,dy in ((-1,-1),(0,0),(255,255)):
   cases.append(dict(round=r,wide=wide,x=((cell%columns)*256-112+dx)&65535,y=((cell//columns)*256-144+dy)&65535,player=cell&1))
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(s,'checkpoint-oracle',args);report['cases']=cases;(ROOT/'reference/checkpoint_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases))
