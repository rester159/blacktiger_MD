import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases={'body':[dict(clear=t,kind=k,template=template) for k,template in enumerate((0x8adc,0x8b0c,0x8ca4,0x8c74)) for t in (0,3,12,44)],'spawns':[]}
for x,y in ((128,96),(0,0),(255,255),(256,96),(-1,96),(128,256),(128,-1)):
 for dx in (-65,-64,-63,0,63,64):
  for dy in (-11,-10,-9,0,9,10):cases['spawns'].append(dict(x=x,y=y,px=x+dx,py=y+dy))
cases['spawns']=[dict(c,kind=k,constructor=pc) for k,pc in enumerate((0x8a5d,0x8a03,0x8b9b,0x8bf5)) for c in cases['spawns']]
args='return {'+','.join(k+'={'+','.join('{'+','.join(f'{key}={v}' for key,v in c.items())+'}' for c in rows)+'}' for k,rows in cases.items())+'}\n'
lines,report=run_oracle(s,'eruption-oracle',args);report['cases']=cases
(ROOT/'reference/eruption_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
