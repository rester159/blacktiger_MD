#!/usr/bin/env python3
"""Catch second-boundary stalls, partial PLAY seconds and lost logic ticks."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from cadence_stats import cadence_stats

def row(presentation=1,play=1,discarded=0):
    return [play,presentation,1]+[0]*10+[discarded]
# Two clock-aligned 30-FPS seconds conceal a whole rolling second with no frame.
trace=[row() for _ in range(30)]+[row(0) for _ in range(60)]+[row() for _ in range(30)]
r=cadence_stats(trace)
assert [s['fps'] for s in r['seconds']]==[30,30]
assert r['worst_rolling_second']==0 and r['seconds_below']['30']==0
assert r['rolling_fps'][30]==0
assert r['seconds_below']['40']==2 and r['longest_consecutive_seconds_below']['40']==2
# Interruptions/partial final seconds are excluded, never extrapolated to 60 FPS.
trace=[row(0,discarded=2) for _ in range(60)]+[row(play=0)]+[row() for _ in range(64)]
r=cadence_stats(trace)
assert [s['fps'] for s in r['seconds']]==[0,None,None]
assert r['seconds'][0]['discarded_ticks']==120
assert r['complete_play_seconds']==1 and r['seconds_below']['30']==1
assert r['longest_consecutive_seconds_below_30']==1
# Legacy traces without debt samples must report unknown, not zero.
assert cadence_stats([row()[:13] for _ in range(60)])['seconds'][0]['discarded_ticks'] is None
assert cadence_stats([])['worst_rolling_second'] is None
print('Cadence statistics: boundary stalls, partial seconds and debt checks passed.')
