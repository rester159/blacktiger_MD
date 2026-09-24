#!/usr/bin/env python3
"""Prevent recurrence of the measured multi-refresh collision-check stalls."""
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from profile_encounters import locations,measure
cases=[]
for name,floor,worst in [('l2_1568_224',430,24),('l3_320_1664',470,25)]:
    scene=next(c for c in locations() if c['name']==name)
    result=measure(scene,ROOT/'out/release/rom.bin',ROOT/'out/release/symbol.txt',600)
    assert result['play_refreshes']==600
    assert result['presentations']>=floor and result['worst_second']>=worst,result['name']
    assert result['pacing_discarded_ticks']==result['vblank_flush_overruns']==result['video_cache_faults']==0
    cases.append({k:v for k,v in result.items() if k not in ('trace','sampled_costs')})
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),cases=cases,scope='Two measured heavy encounter regressions; passing does not imply 60 FPS or acceptable performance across all levels.')
(ROOT/'reports/encounter-pacing-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
