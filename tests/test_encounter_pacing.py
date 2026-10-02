#!/usr/bin/env python3
"""Prevent recurrence of the measured multi-refresh collision-check stalls."""
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from profile_encounters import locations,measure
cases=[]
failures=[]
for name,floor,worst in [('l2_1568_224',430,24),('l3_320_1664',470,25)]:
    scene=next(c for c in locations() if c['name']==name)
    result=measure(scene,ROOT/'out/release/rom.bin',ROOT/'out/release/symbol.txt',600)
    if result['play_refreshes']!=600:failures.append(f'{name}: expected 600 PLAY refreshes, got {result["play_refreshes"]}')
    if result['presentations']<floor or result['worst_second']<worst:
        failures.append(f'{name}: presentations {result["presentations"]}/{floor}, worst second {result["worst_second"]}/{worst}')
    if result['pacing_discarded_ticks'] or result['vblank_flush_overruns'] or result['video_cache_faults']:
        failures.append(f'{name}: discarded ticks/overruns/cache faults: {result["pacing_discarded_ticks"]}/{result["vblank_flush_overruns"]}/{result["video_cache_faults"]}')
    cases.append({k:v for k,v in result.items() if k not in ('trace','sampled_costs')})
report=dict(passed=not failures,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),cases=cases,failures=failures,scope='Two measured heavy encounter regressions; passing does not imply 60 FPS or acceptable performance across all levels.')
(ROOT/'reports/encounter-pacing-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
assert not failures,failures
