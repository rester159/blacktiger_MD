"""Observe the original boss-health row for all eight stages and every layer count."""
import json
from arcade_source import ROOT,Source
from oracle_runner import run_oracle
s=Source();lines,report=run_oracle(s,'boss-hud-oracle')
report['scope']='Original fixed 5D6D boss HUD routine, every stage and remaining layer count. Controlled source calls; not a natural playthrough.'
report['cases']=len(lines)-1
(ROOT/'reference/boss_hud_oracle.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
