#!/usr/bin/env python3
"""Reject ROM payloads and generated/distribution files in the current Git index."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
violations=[]
for name in filter(None,paths):
 p=Path(name)
 if (p.parts[0] in ('dist','screenshots','out','.local','.venv') or
     name.startswith(('assets/source/','assets/ui/','res/generated/')) or
     (p.parts[0] in ('reference','reports') and p.suffix!='.md') or
     (p.parts[0]=='src' and p.suffix=='.inc') or
     name in ('src/data.c','src/actor_dispatch.c','inc/assets.h','res/assets.res','res/assets.h','src/sega_chant.c','src/sega_logo_shinobi.c','src/capcom_logo.c') or
     p.suffix.lower() in ('.bin','.rom','.zip','.wav','.mp3','.gif','.gz')):
  violations.append(name)
if violations:
 sys.exit('Source-only index contains private/generated files:\n'+'\n'.join(violations))
print('Source-only index audit passed.')
