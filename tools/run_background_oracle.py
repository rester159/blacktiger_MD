import json
from arcade_source import Source,ROOT
from extract_bonus import extract
from oracle_runner import run_oracle
s=Source();data=extract(s);cases=[dict(round=r,alternate=a) for r in range(8) for a in (0,1)]
args='return {'+','.join('{round=%d,alternate=%d}'%(c['round'],c['alternate']) for c in cases)+'}\n'
lines,report=run_oracle(s,'background-oracle',args)
expected=[]
for i,c in enumerate(cases):
 tick=0
 for step in range(24):
  phase=step%8
  for w in data['rounds'][c['round']]['background'][c['alternate']][phase]:
   expected.extend([f"WRITE|{i}|{tick}|{w['offset']}|{w['tile']&255}",f"WRITE|{i}|{tick}|{w['offset']+1}|{w['tile']>>8}"])
  delay=10 if phase%4==3 else 1
  expected.append(f'WAIT|{i}|{tick}|{phase}|{delay}');tick+=delay
assert lines[:-1]==expected,next(((a,b) for a,b in zip(lines,expected) if a!=b),('length',len(lines),len(expected)))
report.update(passed=True,cases=cases,yield_checks=16*24,byte_writes=sum(v.startswith('WRITE') for v in expected),scope='Original background task and banked writes for every round/latch state over three cycles. Scheduler yields intercepted; exact task-relative waits, not whole-board interrupt/task timing.')
(ROOT/'reference/background_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('passed','yield_checks','byte_writes')}))
