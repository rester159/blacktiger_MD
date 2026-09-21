"""Capture original shop assets; this tool never runs in the cartridge."""
import json
from arcade_source import ROOT,Source
from oracle_runner import run_oracle
_,report=run_oracle(Source(),'shop-screen-oracle')
report['scope']='Shop task invoked after game initialization. Scheduler yields bypassed; panel characters, colors and ten item sprites observed. Not a timing or natural-entry oracle.'
(ROOT/'reference/shop_screen_oracle.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
