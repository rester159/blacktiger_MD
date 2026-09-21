import json,shutil,hashlib
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
lines,report=run_oracle(Source(),'title-oracle')
path=ROOT/'assets/ui/title_arcade.png';path.parent.mkdir(exist_ok=True)
shutil.copyfile(ROOT/'reports/title-oracle/snap/title-0600.png',path)
report['source_png_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
(ROOT/'reference/title_oracle.json').write_text(json.dumps(report,indent=2)+'\n')
print(len(lines))
