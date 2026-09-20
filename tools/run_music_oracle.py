"""Offline observation of music data; no arcade instructions enter the cartridge."""
import json,sys
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
command=int(sys.argv[1],0) if len(sys.argv)>1 else 0x21
lines,report=run_oracle(Source(),'music-oracle',f'return {{command={command}}}')
report.update(command=command,structure=lines[0],writes=len(lines)-2)
folder=ROOT/'reference/music';folder.mkdir(exist_ok=True)
(folder/f'{command:02x}.json').write_text(json.dumps(report,indent=2)+'\n')
(folder/f'{command:02x}.txt').write_text('\n'.join(lines)+'\n')
(ROOT/'reference/music_oracle_events.txt').unlink();print(report)
