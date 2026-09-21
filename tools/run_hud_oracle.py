"""Capture the original arcade HUD character and palette memory."""
import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
lines,report=run_oracle(Source(),'hud-oracle')
(ROOT/'reference/hud_oracle.json').write_text(json.dumps(report,indent=2)+'\n')
print(len(lines))
