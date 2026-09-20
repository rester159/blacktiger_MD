import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
_,report=run_oracle(Source(),'clear-screen-oracle')
report['scope']='Seven original bonus maps, character planes and palettes after source setup and queued text handler. Round palette initialized from source lists; scheduler yields bypassed. No fade/timing or full-game claim.'
(ROOT/'reference/clear_screen_oracle.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
