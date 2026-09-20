import itertools,json
from arcade_source import Source,ROOT
from extract_bonus import extract
from oracle_runner import run_oracle
s=Source();data=extract(s);cases=[]
for jumping,falling,returning,flags in itertools.product((0,1,255),repeat=4):
 cases.append(dict(kind=0,jumping=jumping,falling=falling,returning=returning,flags=flags))
for r,alternate,x in itertools.product(range(8),(0,1),(0,31,32,223,224,255,256,511,65535)):
 cases.append(dict(kind=1,round=r,alternate=alternate,x=x,y=777,saved_x=1234,saved_y=567))
args='return {'+','.join('{'+','.join(f'{k}={v}' for k,v in c.items())+'}' for c in cases)+'}\n'
lines,report=run_oracle(s,'bonus-oracle',args)
for line in lines[:-1]:
 fields=line.split('|');c=cases[int(fields[1])];actual=list(map(int,fields[2:]))
 if c['kind']==0:
  enabled=not(c['jumping'] or c['falling'] or c['returning'])
  expected=[int(enabled),c['flags']|2 if enabled else c['flags'],0 if enabled else 1,11 if enabled else 0]
 else:
  r=data['rounds'][c['round']]
  if c['alternate']:expected=[c['saved_x'],c['saved_y'],c['saved_x'],c['saved_y'],1,0x21+c['round']]
  else:expected=r['camera']+[(c['x']&0xff00)|((c['x']+r['return_x_low_add'])&255),c['y'],1,0x2d]
 assert actual==expected,(c,actual,expected)
report.update(cases=cases,passed=True,scope='Original contact gate and camera branch; scheduling/audio calls skipped. Tile lists statically extracted, not runtime-verified.')
(ROOT/'reference/bonus_oracle.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=True,cases=len(cases))))
