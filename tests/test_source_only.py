#!/usr/bin/env python3
"""Validate ROM requirements and transactional importing without shipping fixtures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from arcade_source import Source
from import_rom import read_set
manifest=json.loads((ROOT/'assets/rom_manifest.json').read_text())
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder)
 try:Source(tmp)
 except ValueError as error:assert 'Original Black Tiger ROM set required' in str(error)
 else:raise AssertionError('Missing ROM accepted')
 # A caller-controlled manifest must not override the pinned repository hashes.
 (tmp/'payload').mkdir();(tmp/'source_lock.json').write_text('{"files": []}')
 row=manifest['files'][0];(tmp/'payload'/row['path']).write_bytes(bytes(row['size']))
 try:Source(tmp)
 except ValueError as error:assert 'Wrong ROM revision' in str(error)
 else:raise AssertionError('Tampered source package accepted')
 bad=tmp/'bad.zip'
 with zipfile.ZipFile(bad,'w') as z:z.writestr(row['path'],bytes(row['size']))
 destination=tmp/'destination';destination.mkdir();sentinel=destination/'keep';sentinel.write_bytes(b'unchanged')
 result=subprocess.run([sys.executable,str(ROOT/'tools/import_rom.py'),str(bad),'--destination',str(destination)],capture_output=True,text=True)
 assert result.returncode and sentinel.read_bytes()==b'unchanged' and list(destination.iterdir())==[sentinel]
 result=subprocess.run(['make','check-rom'],cwd=ROOT,env=dict(os.environ,BLACKTIGER_SOURCE=str(tmp/'missing')),capture_output=True,text=True)
 assert result.returncode and 'Original Black Tiger ROM set required' in result.stdout+result.stderr
print('Source-only checks passed: missing/corrupt ROM rejection, pinned manifest, failed import leaves existing files intact, Make ROM gate.')
