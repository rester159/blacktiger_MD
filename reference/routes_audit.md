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

## Omitted-wall diagnostic and predictive input search

`find_routes.py --open-walls` runs a separately labelled diagnostic with the
source hidden-wall collision patches already open. It records both original and
modified collision hashes and writes to `reports/routes-open-walls/`. The
400,000-state scans still did not find routes for rounds 2–5. This does not
establish an impassable level: the search is approximate and still excludes
other interactions. Production collision was not changed.

`tools/play_route.py` explores short controller sequences in copies of the
actual emulator process, using `fork` (Unix/macOS). Four candidate processes run
at a time. The parent emulator never rewinds or receives RAM writes. Forecasts
use the terrain plan after the initial candidate input interval; scoring balances
route progress, health/armor and inflicted damage. Only chosen controller inputs
are appended to the final tape. Jump and attack presses are pulsed; lack of route
progress stops the controller after 32 decisions.

Standard libretro savestate exploration was rejected because its chosen input
tape did not reproduce the explored terminal state from a fresh boot. No
conclusion about game correctness relies on that attempt. Process-copy runs
are checked by replaying their tape from the title and comparing persistent 68000 RAM through the SGDK heap boundary, including
game/private subsystem state, and CPU PC/SR/SP. Reserved stack scratch bytes
are excluded: 22 such bytes differed between two independent fresh-boot runs
of the same tape while persistent RAM and the native game state matched.
This check does not claim bit-identical stack contents. The verified replay
hashes and outcome are saved even if verification fails; failure exits nonzero.

The bounded controller currently stalls in round one near a ladder/platform
transition. It is not a competent full-game player, and its failures are not
proof of a port defect or an unreachable route. `--resume` reconstructs a
previous verified tape from boot before searching more inputs; `--fight-boss`
allows exploration to continue after a boss spawns. Neither flag grants health,
inventory, coordinates, progress or other game-state changes.

```sh
.venv/bin/python tools/find_routes.py --round 2 --round 3 --round 4 --round 5 --open-walls --limit 400000
.venv/bin/python tools/play_route.py --steps 200 --horizon 64 --damage-weight 2
```
