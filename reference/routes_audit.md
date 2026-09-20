# Native route investigation

`tools/find_routes.py` builds the existing C movement and bonus routines as a
host library. `route_model.c` supplies map collision and lifecycle glue; the
contact function and generated alternate-area definitions are copied directly
from the current production sources during compilation. Search states include
player motion and persistent alternate-area state. Found routes are replayed
from their initial state and compared byte-for-byte at every endpoint.

The search uses bounded weighted A* and coarsens its visited-state key. It
excludes combat, attacks, breakable walls, shops, damage, respawns, and boss
victory. Out-of-bounds movement candidates are rejected rather than clamped.
A found path proves only model reachability of a boss vicinity; a failed search
does not prove the actual map unreachable. Initial scans used eight-update
actions/eight-pixel cells; unresolved rounds were refined to four updates/four
pixels. Per-round limits, results and collision hashes are in the JSON reports.

Terrain paths currently exist for rounds 1, 6, 7 and 8. Rounds 2 and 3 reach the
one-million-state cap; rounds 4 and 5 exhaust their coarsened frontiers. The next
route work must investigate omitted interactions and state pruning before
changing production terrain or movement. Do not weaken collision merely to make
this search pass.

`tools/replay_route.py` replays a round-one plan in Genesis Plus GX from the
title screen. It never writes RAM or loads savestates. It records actual input
masks per video frame, the trajectory, resources and exit reason. A second
fresh boot must reproduce the same final native game state. The default replay
currently dies before the boss; natural full-game completion remains unproven.
Optional airborne attack changes motion and may diverge from a terrain-only
plan; its policy is recorded explicitly.

The investigation found a prototype-only C-button screen attack with two charges.
It has been removed. The supplied source input decoder uses attack/jump bits
10/20; the [MAME driver input definition](https://github.com/mamedev/mame/blob/master/src/mame/capcom/blktiger.cpp#L552-L560)
also identifies only two player buttons. The original POW pickup effect remains
on its existing source-backed path. `test_controls_runtime.py` compares a real
180-frame movement/jump/attack sequence with and without repeated C presses.

Commands:

```sh
.venv/bin/python tools/find_routes.py --limit 400000
.venv/bin/python tools/find_routes.py --round 2 --round 3 --round 4 --round 5 --limit 1000000 --ticks 4 --quantum 4
.venv/bin/python tools/replay_route.py
```
