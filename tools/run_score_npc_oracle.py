"""Verify original score formatting and movement-dependent rescue contact."""
import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source()
s.expect(None,0x4995,'3a12f4473a18f44f3a16f4b0b1c0')
s.expect(None,0x0568,'3600cbd471cb94c9')
lines,report=run_oracle(s,'score-npc-oracle')
for line in lines[:-1]:
 tag,value,result=line.split('|');value=int(value)
 assert result==(str(int(value==0)) if tag=='CONTACT' else str(value*10).rjust(9)),line
report.update(passed=True,contact_cases=8,score_cases=7,witnesses=list(s.witnesses.values()))
(ROOT/'reference/score_npc_oracle.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
