# Breakable pots

The native port now includes the fixed-ROM `7138` pot constructor that the
ordinary actor extractor previously skipped. `tools/extract_pots.py` derives
all graphics, contents and coordinates locally from the owner-supplied Black
Tiger ROM; none of those generated assets belong in Git.

## Source behavior

- Bank-5 level lists, addressed through fixed `1E07`, contain 251 unique pot
  placements: 26, 32, 32, 32, 32, 32, 33 and 32 for levels 1–8.
- Each placement retains its original persistence ID (1–32). Level 7 has two
  placements sharing ID 31. They must not produce independent rewards.
- Fixed `242A` copies the level's 32-byte bank-6 `B718` contents table and
  performs 16 swaps. Each index uses the original byte rotates; each swap
  yields two RNG updates. The native RNG/shuffle is compared against the
  actual Z80 routine in MAME, across eight levels and sixteen seeds.
- Pot shuffling precedes chest shuffling, as at fixed `1E38`/`1E46`. Contents
  are preserved on checkpoint restart. Exact global arcade scheduling/RNG
  phase is not claimed; matching seeds produce matching pot contents.
- Fixed `71E4` decrements a two-hit counter regardless of weapon strength.
  The first hit selects the cracked sprite; the second selects the source
  break sequence. Offline conversion retains original frame durations,
  palette indices, interleaved item frames and event boundaries.
- `7222` marks an opened pot. Currency, keys and time remain until collected;
  they do not become ordinary expiring enemy drops. Collection uses the
  source small-actor contact bounds and odd-frame contact phase.
- Currency contents award 5, 10, 50, 100, 500 or 1000 Zenny. Keys cap at 99;
  time items add 30 seconds. Break/collection score increments follow the
  source score-table offsets. Empty pots give no item.
- `7261` creates the original puff; `72AA` dispatches one of four enemy
  constructors at the original (-8,-16) offset. Existing native crawler,
  statue, stone and reinforcement implementations supply their behavior.
  `7251` marks a completed trap/empty break as consumed.

## Native ownership

Pots have a separate 33-entry pool, so their presence does not displace the
port's ordinary level actors. Spawn scanning is divided across four ticks;
updates/rendering use a conservative active upper bound. Trap enemies share
the existing actor pool. Spawn bookkeeping slot 159 is reserved for transient
pot enemies; extraction asserts that all real spawn tables remain below it.
The native pool limits are not a reproduction of the original shared Z80 pool.

## Verification

- `tests/test_pots.py`: 128 native/original-ROM shuffle comparisons.
- `tests/test_pots_runtime.py`: two-hit breakage, actual attack-button input,
  all contents/rewards, four trap families, retirement and death persistence.
- `tests/test_pot_placements_runtime.py`: cartridge visits to all 251 source
  positions, including shared-ID suppression.

Run `make references` to regenerate ignored oracle observations, then run the
above tests (also included in `make test`). Screenshots and binaries remain local.
