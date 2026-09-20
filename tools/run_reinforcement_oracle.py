import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
# Both constructors have the same complete pre-allocation byte sequence.
assert s.read(2,0x8344,0x44)==s.read(2,0x9af6,0x44).replace(bytes.fromhex('279b'),bytes.fromhex('7583')).replace(bytes.fromhex('379b'),bytes.fromhex('8583'))
for pc in (0x8344,0x9af6,0x8ef4):
 for x,y in ((128,96),(0,0),(255,255),(256,96),(-1,96),(128,256),(128,-1)):
  for dx in (-49,-48,-47,0,47,48):
   for dy in (-33,-32,-31,0,31,32):
    cases.append(dict(constructor=pc,x=x,y=y,px=x+dx,py=y+dy,primary=0,delay=0,waiting=0,attempts=0,full=0,ticks=43))
 for delay,waiting,attempts in ((39,1,1),(255,1,1),(0,0,255),(0,0,1)):
  for primary in (0,1,2,3):
   for full in (0,1):cases.append(dict(constructor=pc,x=128,y=96,px=128,py=96,primary=primary,delay=delay,waiting=waiting,attempts=attempts,full=full,ticks=43))
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(s,'reinforcement-oracle',args);report['cases']=cases
(ROOT/'reference/reinforcement_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
