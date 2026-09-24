# v27: all-level performance pass toward a 40-FPS floor

**The 40-FPS floor is not reached.** Across 229 ten-second encounter cases (226 unique positions) covering all eight levels, the worst rolling second improves from 12 to 15 presentations. Each level’s survey minimum improves. Sixteen additional one-minute encounter traces expose sustained slowdowns; some have more seconds below 40 despite improved minima. No scene average is used to establish a floor.

Cartridge: [blacktiger_MD_v27.bin](../dist/blacktiger_MD_v27.bin) · [Validation](v27-validation.json).

## Second-by-second measurements

- [Eight original sustained fixtures: interactive chart](per-second-v27.html) · [CSV](per-second-v27.csv)
- [Eight additional difficult fixtures: interactive chart](per-second-extra-v27.html) · [CSV](per-second-extra-v27.csv)
- [All 229 survey cases: interactive chart](per-second-survey-v27.html) · [CSV](per-second-survey-v27.csv)

Each chart provides fixed seconds and rolling one-second windows, a 40-FPS threshold, lost simulation ticks and the longest consecutive run below 40. One second is 60 emulated NTSC refreshes; counts are native graphics submissions, not host display delivery. Interrupted PLAY windows remain blank. Before and after use the same starting fixtures and controls, but missed simulation ticks can cause later game states to diverge. These are injected encounters, not complete natural playthroughs.

### Broad survey

| Level | Worst rolling second v26 → v27 | Common complete seconds below 40 | Dropped logic ticks |
|---|---:|---:|---:|
| 1 | 30 → 31 | 7 → 4 | 0 → 0 |
| 2 | 21 → 22 | 10 → 9 | 0 → 0 |
| 3 | 20 → 22 | 16 → 15 | 0 → 0 |
| 4 | 17 → 18 | 65 → 57 | 13 → 2 |
| 5 | 18 → 21 | 16 → 15 | 2 → 0 |
| 6 | 16 → 19 | 34 → 25 | 14 → 0 |
| 7 | 12 → 15 | 49 → 44 | 218 → 93 |
| 8 | 15 → 18 | 41 → 36 | 35 → 5 |

### Original one-minute fixtures

| Level | Worst rolling second v26 → v27 | Common complete seconds below 40 | Dropped logic ticks |
|---|---:|---:|---:|
| 1 | 34 → 35 | 4 → 2 | 0 → 0 |
| 2 | 18 → 18 | 15 → 16 | 4 → 2 |
| 3 | 21 → 22 | 4 → 6 | 0 → 0 |
| 4 | 18 → 19 | 41 → 31 | 8 → 0 |
| 5 | 29 → 34 | 4 → 3 | 0 → 0 |
| 6 | 20 → 25 | 9 → 9 | 0 → 0 |
| 7 | 13 → 15 | 35 → 26 | 168 → 41 |
| 8 | 15 → 18 | 15 → 14 | 30 → 5 |

### Additional one-minute fixtures

| Level | Worst rolling second v26 → v27 | Common complete seconds below 40 | Dropped logic ticks |
|---|---:|---:|---:|
| 1 | 30 → 31 | 1 → 1 | 0 → 0 |
| 2 | 19 → 22 | 6 → 9 | 0 → 0 |
| 3 | 20 → 25 | 5 → 3 | 0 → 0 |
| 4 | 17 → 19 | 12 → 9 | 6 → 1 |
| 5 | 18 → 19 | 23 → 23 | 2 → 0 |
| 6 | 16 → 19 | 18 → 18 | 14 → 0 |
| 7 | 12 → 15 | 29 → 35 | 107 → 30 |
| 8 | 17 → 18 | 42 → 40 | 27 → 0 |

The survey’s total discarded ticks fall from 282 to 100. In the original level-7 fixture they fall from 168 to 41, but its 15-FPS minimum still misses the target badly. The additional level-7 fixture spends 35 common complete seconds below 40 versus 29 before. Original level-2 and level-3 fixtures also have more below-40 seconds. These mixed results are retained in the charts and tables rather than hidden behind aggregate speedups.

## Retained changes

- Scroll updates handle camera movement of up to four tiles incrementally, avoiding a full map reload for three- or four-tile catch-up moves.
- The scheduler can prepare the next logic tick during available VBlank waiting time after three catch-up ticks, with existing mode/reload guards and the fixed simulation clock preserved.
- Weapon contact skips actor types that cannot take weapon hits. Generated family dispatch replaces a long sequence of damage-handler probes.
- Projectile pools track a conservative last occupied slot, avoiding repeated scans of unused trailing slots while retaining original collision order.
- Twelve enemy families take a short path when an animation remains on its current frame. Motion still runs on those ticks; state transitions and animation timing retain their source behavior.

An experimental dagger bounding envelope passed contact comparisons but worsened measured cadence and was removed. CPU sampling identifies simulation catch-up, weapon contact and sprite construction as continuing bottlenecks. Reaching 40 still requires substantial work in those paths; this pass does not establish that the target is achievable with the current rendering architecture.

## Validation and scenery

All 157 `make test` commands pass, and strict packaging checks match the final ROM hash. Coverage includes original actor animation/motion traces, 50,000 randomized weapon-contact comparisons, scheduler/frame pacing, incremental scroll cache checks, damage and projectile behavior. The scroll regression now covers up to four-tile diagonal movements across all eight levels. Presentation comparisons have 3,250 fixed-second rows across the three CSVs, including interrupted windows.

No new art is introduced. Level 6 keeps its full original scenery map with parallax disabled, and the regression checks all 2,097,152 source-converted pixels. Parallax remains limited to levels 4, 5, 7 and 8. No hardware overclock, actor-count reduction or intentional simulation-rate reduction is used. Existing overload can still discard simulation ticks, as reported above. Physical-hardware and full-playthrough validation remain outstanding.

ROM SHA-256: `99a0d493b451ea06487e0ccd75ec4bde3e12c1273eb04307a954ffa82f4e5ad6`.

---

# v26: restore original level 6 scenery

Level 6 now uses its original complete world-map artwork with parallax disabled. The temple appears once in its original top-of-level location; all original islands, clouds and mist retain their source positions. The v25 repeating temple/rock composition is removed. No new art or palette changes are introduced, and the HUD remains transparent.

Cartridge: [blacktiger_MD_v26.bin](../dist/blacktiger_MD_v26.bin). [Temple preview](v26-level6-temple.png) · [Island preview](v26-level6-islands.png) · [Original-map regression](level6-original-runtime-tests.json) · [Validation](v26-validation.json).

The source regression compares all 2,097,152 level-6 map pixels after Genesis palette conversion, then checks native VRAM through horizontal and vertical scrolling in temple, island and cloud locations. Level 6 has no active far plane. Levels 4, 5, 7 and 8 retain parallax; [parallax-only preview](parallax-only-v26.png).

## Per-second performance

[Interactive v25 → v26 comparison](per-second-v26.html) · [CSV](per-second-v26.csv) · [raw traces](encounter-seconds-v26.json).

The same eight 3,600-refresh encounter fixtures were rerun. Restoring level 6's full world artwork increases terrain-streaming work: its worst rolling second falls from 25 to 20 presentations, and fixed seconds below 30 rise from 1 to 4; no simulation ticks are dropped in that fixture. Other selected scenes retain their v25 worst-second and below-30 counts. This version prioritizes the requested original scenery layout, not a new performance gain. No stable 30-FPS floor is claimed.

| Level | Worst rolling second v25 → v26 | Common complete seconds below 30 | Dropped logic ticks |
|---|---:|---:|---:|
| 1 | 34 → 34 | 0 → 0 | 0 → 0 |
| 2 | 18 → 18 | 6 → 6 | 4 → 4 |
| 3 | 21 → 21 | 3 → 3 | 0 → 0 |
| 4 | 18 → 18 | 25 → 25 | 8 → 8 |
| 5 | 29 → 29 | 0 → 0 | 0 → 0 |
| 6 | 25 → 20 | 1 → 4 | 0 → 0 |
| 7 | 13 → 13 | 26 → 26 | 168 → 168 |
| 8 | 15 → 15 | 10 → 10 | 30 → 30 |

One second means 60 emulated NTSC refreshes; graphics presentations are counted directly. Fixed seconds and rolling windows are both available, and interrupted PLAY windows are left blank. These are sampled encounters, not full playthroughs or host display timing.

---

# v25: scenery corrections and second-by-second performance

All eight levels retain their original art and palettes. The parallax cleanup uses only existing tiles: level 5 has a trimmed and mirrored source mountain ridge, level 6 has the original temple retiled onto original distant rock tiles, and level 7 has finished source-window silhouettes. Stray gold floor fragments are trimmed from level 8’s far scenery. The opaque level 5/6 HUD bands are removed. Tile edges match in the rebuilt repeating art; original platform contours and collision maps are retained. [Tiled parallax only, levels 4–8](parallax-only-v25.png), [artwork provenance and compilation](../art/backgrounds-v25.md).

**Performance is measured every second, including rolling one-second dips—not judged by scene averages.** The cave's worst rolling second improves from 15 to 18 presentations; level 7 improves from 11 to 13. Level 6 improves from 14 to 25. These are still below a reliable 30-FPS floor. The cave also spends two more fixed seconds below 30, and level 8 has one extra below-30 second and one extra dropped logic tick; this is not an across-the-board improvement.

Cartridge: [`blacktiger_MD_v25.bin`](../dist/blacktiger_MD_v25.bin).

## Second-by-second evidence

[Interactive before/after chart and all seconds](per-second-v25.html) · [CSV](per-second-v25.csv) · [comparison JSON](per-second-v25.json) · [raw v25 traces](encounter-seconds-v25.json).

One 3,600-refresh input schedule from a selected encounter in each level, compared with the exact v24 ROM and saved v24 symbols. Each fixed second contains 60 emulated NTSC refreshes. Rolling windows advance one refresh at a time, exposing dips spanning fixed-second boundaries. Interrupted/partial PLAY seconds remain blank. These count native graphics submissions, not host screen refreshes. The same starting fixtures and controls are used; missed logic ticks can cause later game-state divergence.

| Level | Worst rolling second v24 → v25 | Common complete seconds below 30 | Complete seconds below 20 | Dropped logic ticks |
|---|---:|---:|---:|---:|
| 1 | 30 → 34 | 0 → 0 | 0 → 0 | 0 → 0 |
| 2 | 15 → 18 | 8 → 6 | 4 → 1 | 35 → 4 |
| 3 | 18 → 21 | 8 → 3 | 1 → 0 | 3 → 0 |
| 4 | 15 → 18 | 23 → 25 | 7 → 4 | 38 → 8 |
| 5 | 26 → 29 | 1 → 0 | 0 → 0 | 0 → 0 |
| 6 | 14 → 25 | 18 → 1 | 5 → 0 | 30 → 0 |
| 7 | 11 → 13 | 32 → 26 | 19 → 13 | 218 → 168 |
| 8 | 15 → 15 | 9 → 10 | 6 → 4 | 29 → 30 |

For the cave, the longest consecutive run of fixed seconds below 30 falls from 8 to 6. Severe seconds below 20 fall from 7 to 4. The retained change improves the deepest stalls and simulation debt, while the full timeline shows its mixed behavior around 30 FPS. Level 7's seconds below 20 fall from 19 to 13; its longest below-30 run remains 9 seconds.

## Retained implementation changes

- Fast animation updates for held frames skip unnecessary interpreter calls; transitions retain the original interpreter.
- Loot updates/render scans stop after the last potentially active slot, skipping empty pools.
- Generated actor update classes reduce repeated type dispatch.
- Weapon contact rejects inactive and irrelevant dagger slots before expensive vulnerability checks while retaining contact order.
- Repeatable tiles compile offline. Level 6's far artwork uses 104 unique patterns instead of 266; no new per-frame bitmap drawing is added.

Several trial implementations were rejected after second-by-second comparisons showed longer slow stretches elsewhere. No CPU overclock or emulator frameskip was introduced.

## Validation and scope

See [v25 validation](v25-validation.json) for the final ROM hash and full regression result. Dedicated checks cover 6 million animation comparisons, 50,000 weapon-contact trials, 20,000 terrain-strip trials, live scenery palettes and eight camera positions per level, transparent HUD composition, parallax shifts, shop restoration, cache integrity and rebuilt scenery seams. The eight sustained traces report no video cache faults or VBlank flush overruns.

[All eight scenery palettes and collision maps match v24 byte for byte](scenery-source-preservation-v25.json).

The visual review and performance routes are sampled coverage, not complete playthroughs. Lower frame rates remain possible outside these fixtures. Only existing art is trimmed and retiled within the existing Genesis tile/palette limits; screenshots show the actual ROM output.

---

## Historical v24 report

# Resumed optimization: v23 → v24

The reported cave encounter now averages **34.15 FPS, up from 30.22 FPS (+13.0%)** over the same 3,600-refresh input schedule. Its worst rolling second rises from 14 to 15 presentations, and dropped simulation ticks fall from 94 to 38. The lowest average among the eight selected sustained encounters rises from **26.05 to 31.20 FPS** (level 7). These are measured improvements, not a guaranteed 30-FPS floor: severe short dips remain.

Tested cartridge: [`dist/blacktiger_MD_v24.bin`](../dist/blacktiger_MD_v24.bin). The launcher now selects this version. Historical v22 → v23 results remain below.

## Changes retained

1. Walk terrain rows/columns directly, reusing map and ring-buffer coordinates instead of calling the full scalar resolver for every tile. Dynamic hidden/bonus tiles and backdrop remaps retain the same resolution rules. Pin every exposed strip before allocating patterns, as before.
2. Route hidden walls, captives and chests through a small dedicated update routine. Preserve hit timers, retirement, pre-movement contact, rescue and reward behavior.
3. Share the boss presence/input-lock scan within a simulation tick. Actor updates and weapon damage occur after both consumers; layered-boss queries keep their native semantics.
4. Keep wisp/crawler/zombie updates and sprite-piece cache misses out of their callers' inlined code, reducing register-save and dispatch overhead on the 68000. Check mode changes after active actor updates rather than after empty slots.

Simulation scheduling, AI update rate, collisions, scenery, parallax, sprite budgets and Debug behavior are unchanged. No CPU overclock or emulator frameskip was introduced.

## Sustained comparison

Same eight positions and input schedules as the v23 report, 3,600 NTSC refreshes per scene. Means use only continuous PLAY, normalized to 60 refreshes. “Worst second” counts presentations in a rolling 60-refresh PLAY window.

| Level | Mean FPS v23 → v24 | Worst second v23 → v24 | Dropped logic ticks v23 → v24 |
|---|---:|---:|---:|
| 1 | 53.83 → 56.07 | 17 → 30 | 5 → 0 |
| 2 | 42.74 → 49.28 | 14 → 15 | 97 → 35 |
| 3 | 54.10 → 50.43 | 14 → 18 | 19 → 3 |
| 4 | 30.22 → 34.15 | 14 → 15 | 94 → 38 |
| 5 | 49.97 → 53.15 | 23 → 26 | 0 → 0 |
| 6 | 26.97 → 37.00 | 14 → 14 | 138 → 30 |
| 7 | 26.05 → 31.20 | 11 → 11 | 391 → 218 |
| 8 | 44.04 → 48.73 | 16 → 15 | 54 → 29 |

Seven scene means improve; level 3 falls from 54.10 to 50.43 FPS, although its worst second improves and discarded ticks decrease. Level 7's worst second remains 11. Identical controller schedules do not guarantee identical later game states: CPU savings change missed-tick debt, movement, rescue timing and actor populations. These are live encounter comparisons, not frozen-workload microbenchmarks.

## Broader survey and validation

- Repeated all **229 source-position samples** at 600 refreshes each. There are 226 unique location names; three duplicate positions are retained to match the historical survey and its weighting.
- Across **163 samples that stay in PLAY throughout both versions**, the unweighted mean of scene means rises from **49.24 to 52.68 FPS**. 144 improve, 7 are unchanged, and 12 regress. This is not a whole-game average.
- Largest survey regressions: `l8_1792_224` 56.6 → 52.4, `l8_736_224` 47.7 → 43.7, and `l3_576_800` 57.9 → 54.1 FPS. All regressions are retained in the comparison JSON.
- Zero observed graphics-flush overruns or terrain-cache faults across the survey and eight sustained runs.
- Full `make test` passed (152 Python commands), followed by the package tool's exact-ROM/hash checks. Additional terrain-strip differential test: **20,000 cases**, with address/undefined-behavior sanitizers, covering pin/unpin reference counts, world/ring wrapping, out-of-map Y, dynamic rows and backdrop remapping.
- The installed RetroArch core reproduced **every trace row** of the 3,600-refresh cave and level-7 runs. This verifies core-level behavior, not macOS display delivery or physical Genesis performance.

The remaining problem is sustained dense simulation/rendering work, especially in level 7; 218 simulation ticks are still discarded in its selected one-minute run. Short presentation stalls remain well below the scene averages. Further work should target those workloads without reducing gameplay fidelity.

## Reproduce v24

```sh
make test
.venv/bin/python tests/test_terrain_strips.py
.venv/bin/python tools/profile_encounters.py --frames 600 --output reports/encounter-profile-v24.json
.venv/bin/python tools/profile_encounters.py --scene l4_1856_416 --scene l7_1312_256 --frames 3600 --output reports/cave-and-level7-v24.json
.venv/bin/python tools/package.py --name blacktiger_MD_v24.bin
```

Baseline v23 symbols are preserved in `reports/symbols-v23.txt`; pair them with `dist/blacktiger_MD_v23.bin` for baseline reruns. Current symbols are packaged in `dist/symbols.txt`.

Evidence: `reports/encounter-profile-v24.json`, `reports/encounter-sustained-v24.json`, `reports/cpu-encounters-v24.json`, `reports/user-core-performance-v24.json`, `reports/performance-comparison-v24.json`, `reports/terrain-strip-tests.json`, and `reports/v24-validation.json`.

v24 ROM SHA-256: `6c6e7804c67e3339e0dd01f79283baf2d18d898ee50f8312ad303c77860cd2dc`.

---

# Measured performance: v22 → v23

The broader profile confirms real presentation stalls throughout the maps. The old entrance patrols were not representative. This release is a partial optimization, **not a smooth-60-FPS fix**.

## Measurement

- 229 source-spawn encounter positions across all eight maps, 600 NTSC refreshes each, on both ROMs (about 38 emulated minutes per version).
- Eight additional 3,600-refresh runs per version, selecting the slowest uninterrupted baseline encounter in each level. Some naturally enter rescue/other modes; FPS statistics include only continuous PLAY.
- Starting positions are injected while paused; thereafter real spawning, AI, collisions, jump/climb/attack input and Debug rules run without RAM writes. These are reproducible encounter samples, not full playthroughs.
- Count completed graphics submissions per emulated refresh, retain interval histograms, sliding one-second lows, logic ticks, dropped simulation debt, actor counts, camera/player coordinates and sampled game/video/audio costs. Image-change counts are separate and are not called FPS.
- The host-side CPU hook records 68000 instruction cycles by PC and resolves them against the ROM symbol table. Its exact core hash is checked before using internal offsets. Hooked and unhooked traces matched for all 600 refreshes of the baseline level-2 check; it adds host work, not emulated cycles.
- Your installed RetroArch core produced identical 600-refresh traces for the level-2 and cave comparison scenes. Its settings have frameskip disabled and CPU overclock at 100%. This does not measure macOS/display delivery.
- Existing ROM subtick samples occur every sixteen submissions, include catch-up work and possible interrupts, and exclude the explicit graphics-flush phase. They are supporting diagnostics, not complete per-frame CPU accounting. Instruction attribution also does not account for every external DMA stall.

## Profile-directed changes

1. Decode ordinary actor weapon geometry once per collision pass, reuse it across links/daggers, skip ineligible dagger parity and enumerate active daggers once. Keep screen-byte wrapping, collision ordering and native boss weak-point routines. A differential test compares 50,000 randomized encounters against the pre-batching implementation, with real constructor geometry and scalar collision functions.
2. Route skeleton updates directly and avoid entering the common-family register-heavy routine before falling back to other actor families. Preserve native update/contact order.
3. At horizontal wrap, search two sorted spawn ranges instead of scanning the complete level. Preserve source row order, four-tick activation phase and existing spawn rules.
No scenery, parallax, enemy behavior, simulation rate or debug features were removed.

On the baseline level-2 CPU trace, weapon scanning and dagger contact consumed about 10.6% of attributed cycles. In the slow cave trace, actor-update routines consumed about 21.6%, spawning 6.7%, and weapon scanning/contact 9.2%. Rendering remains a significant cost. Function totals include any compiler-inlined callees; main/VDP wait loops include idle time and are not all useful work.

## Sustained results

One minute per selected scene; FPS is normalized to 60 refreshes. “Worst second” is the minimum rolling 60-refresh presentation count.

| Level | Mean FPS before → after | Worst second before → after | Dropped logic ticks before → after |
|---|---:|---:|---:|
| 1 | 49.25 → 53.83 | 12 → 17 | 65 → 5 |
| 2 | 37.80 → 42.74 | 10 → 14 | 266 → 97 |
| 3 | 42.43 → 54.10 | 11 → 14 | 93 → 19 |
| 4 | 18.28 → 30.22 | 11 → 14 | 604 → 94 |
| 5 | 38.32 → 49.97 | 13 → 23 | 168 → 0 |
| 6 | 24.87 → 26.97 | 9 → 14 | 458 → 138 |
| 7 | 27.05 → 26.05 | 8 → 11 | 444 → 391 |
| 8 | 41.26 → 44.04 | 10 → 16 | 228 → 54 |

All eight selected worst-second rates improve, but the level-7 mean is slightly worse and its heavy workload still drops simulation ticks. Across 164 survey scenes that stayed in PLAY for the complete sample in both versions, the unweighted mean of scene averages rises from 45.69 to 49.14 FPS. This is not a whole-game average.

One survey route (`l4_1136_640`) decreases from 44.3 to 37.1 FPS. The traces show differing routes/populations: the baseline spends 151 refreshes with zero visible actors after falling away, while the new run stays in the occupied area. Keep this case visible; the input schedule is identical, but CPU savings and changed missed-tick debt mean the later game states are not identical.

Remaining work is substantial: dense actor updates, sprite preparation, terrain-strip work and repeated full simulation catch-up still exceed the 68000 budget. The data now exposes those encounters instead of hiding them behind entrance averages. Physical Genesis and host display pacing remain unverified.

## Reproduce

```sh
.venv/bin/python tools/profile_encounters.py --list
.venv/bin/python tools/profile_encounters.py --frames 600 --output reports/encounter-profile.json
.venv/bin/python tools/profile_encounters.py --scene l4_1856_416 --frames 3600 --cpu --output reports/cave-profile.json
```

For an older ROM, pass both `--rom` and its matching `--symbols`. The CPU hook currently supports only the pinned ARM64 Genesis Plus GX test core; cadence-only runs can use `BLACKTIGER_CORE` with a compatible core exposing RAM. The wrapper installs no ROM-side timing instrumentation.

Raw evidence: `reports/encounter-profile-v22.json`, `reports/encounter-profile-v23.json`, `reports/encounter-sustained-v22.json`, `reports/encounter-sustained-v23.json`, `reports/cpu-encounter-v22.json`, `reports/cpu-slow-scenes-v22.json`, `reports/cpu-encounters-v23.json`, and `reports/performance-comparison-v23.json`.

Baseline ROM SHA-256: `2e5a00ac6402999d4b7f4c3e9cab05f21f8c86fc7efff5ba31e90f8215b8a740`.
v23 ROM SHA-256: `eb180e5b03420ca92b3e0a868a0d44f3dd19b64d391ed56a92ba424446cebcc5`.
