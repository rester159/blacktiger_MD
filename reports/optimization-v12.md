# v1.2 final optimization pass

Kept two changes: container/dragon-wave trap pools carry a conservative exclusive upper bound, reducing empty-slot scans in updates, contact checks and drawing; the music player enters the FM writer only when the next event is due. Active entries retain their update order and timing. Music uses the same NTSC/PAL clocks and sends the same register events. No enemy-count, art, animation-rate or simulation-rate reductions were introduced.

## Measurements

Same injected starting locations and controller schedules on the pinned Genesis Plus GX core. The short survey covers 229 encounters at 600 refreshes each; four selected crowded encounters also run for 3,600 refreshes each. Counts are actual presentations per 60 emulated NTSC refreshes, not host display FPS. Input sampling and trajectories can diverge when presentation timing changes, so these are end-to-end route comparisons, not identical-state microbenchmarks. Raw before/after traces retain simulation tick debt and per-second lows.

Across 1984 common complete PLAY seconds, mean presentation FPS is **53.29 → 53.62**; seconds below 30 FPS: **99 → 90**. Scene means improve in 140 cases, remain equal in 54, and regress in 35. The survey's lowest rolling second is **14 → 14 FPS**. Total discarded simulation ticks: 120 → 100. These changes improve throughput but do not eliminate busy-scene stalls.

| Level | Mean FPS before → after | Worst rolling second before → after |
|---|---:|---:|
| 1 | 57.16 → 57.16 | 29 → 30 |
| 2 | 56.36 → 56.56 | 20 → 20 |
| 3 | 54.28 → 54.39 | 19 → 19 |
| 4 | 53.12 → 53.41 | 18 → 19 |
| 5 | 55.44 → 55.69 | 19 → 19 |
| 6 | 51.77 → 52.13 | 18 → 18 |
| 7 | 49.32 → 49.85 | 14 → 14 |
| 8 | 50.81 → 51.56 | 16 → 17 |

### One-minute stress traces

| Scene | Mean FPS before → after | Lowest second before → after | Discarded ticks before → after |
|---|---:|---:|---:|
| l7_1200_704 | 38.78 → 42.77 | 16 → 15 | 30 → 30 |
| l7_1312_256 | 36.37 → 36.75 | 14 → 14 | 57 → 60 |
| l8_272_608 | 47.93 → 48.83 | 16 → 18 | 20 → 3 |
| l8_1680_880 | 28.68 → 32.7 | 18 → 18 | 7 → 4 |

[Interactive second-by-second comparison](optimization-v12-long-cadence.html) · [Summary data](optimization-v12-summary.json)

The CPU profiles on the four initial short encounters put the FM `apply` routine at 1.63–2.16% before and 0.40–0.95% after. This is an exclusive instruction-cycle share; external DMA stalls are not included. Overall route improvements also depend on refresh-boundary crossings and resulting gameplay trajectories.

## Remaining graphics deadline issue

The broad survey records one VBlank upload overrun before and two after, all in `l8_1840_224`; both builds have zero tile-cache faults. Captured start/bytes/DMA operations/end-line values are `(224,4836,39,16)` before, and `(224,4730,30,0)` / `(224,4658,30,255)` after. The shorter optimized bursts still occasionally exceed the display deadline. This is an existing palace streaming limit with changed event frequency, not a resolved problem. The narrower release pacing fixtures do not exercise this exact route. No sprite dropping or art reduction was added to conceal it.

## Validation and reproducibility

The existing trap source-oracle check covers 2,880 ticks. Its additional pool checks cover all four six-piece allocations, full-pool rejection, retirement, reuse and restart. Music validation compares 154,193 sequencing/clock batches across all 25 tracks, both regions, missed-frame batches and loop/end boundaries. The complete release suite and strict package status are recorded in [v1.2 validation](v12-validation.json).

- Raw survey: `optimization-v12-before.json`, `optimization-v12-after.json`.
- Raw long traces: `optimization-v12-long-before.json`, `optimization-v12-long-after.json`.
- CPU samples: `optimization-v12-cpu-before.json`, `optimization-v12-cpu-after.json`.
- Reproduce the survey with `tools/profile_encounters.py --frames 600`; pass the preserved baseline ROM and symbols from `.local/optimization-v12-baseline/` for the before run. Use `--frames 3600` and the four scene names in the table for the longer traces.
- This remains **v1.2**. No v1.3 was created. Physical hardware and a natural full-game playthrough were not tested.

Before SHA-256: `ccc52d0a8b1ea0a7345ca727b5527b46fe7dc091fce6af2283024f0ea5882568`.

After SHA-256: `779228b30278f8fc269f0d7e91467134ab8f00f278a51f469fade5b0f50bc16b`.
