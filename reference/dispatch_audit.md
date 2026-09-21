# Native actor dispatch optimization

The renderer previously evaluated a long sequence of family arrays for every
active actor, then obtained its native animation frame. `actor_dispatch` now
stores a native frame function, sprite layout, and common update-route selector
for each of the 66 actor definitions. The table is compiled offline by
`extract_actor_dispatch.py`; it contains Genesis function pointers, not arcade
program addresses. Legacy fallback animation arithmetic runs only for actors
that actually use that fallback.

The game uses the same descriptor to select common movement/contact handlers.
The existing early layered-boss, paired-actor and dragon paths still precede
shared offscreen cleanup. Remaining handlers retain their original order of
movement, vulnerability checks, damage dispatch and post-movement contact.
Pre-movement contact families retain their separate path.

`test_actor_dispatch.py` checks every linked table entry against the established
family arrays, including frame function, sprite layout and behavior route. The
hazard family uses its source constructor identity because its now-unused legacy
array is removed by the linker. Existing sprite tests check 48 pixel fixtures,
resident VRAM textures and scanline limits. Enemy/body/projectile tests continue
to cover each native family and its cartridge integration.

The 180-video-frame round-entry benchmark is approximate and follows different
amounts of gameplay as throughput improves. Against commit 4c16959 it records:

| Round | Previous logic updates | New logic updates |
|---|---:|---:|
| 1 | 134 | 155 |
| 2 | 168 | 173 |
| 3 | 99 | 119 |
| 4 | 139 | 148 |
| 5 | 154 | 163 |
| 6 | 109 | 123 |
| 7 | 115 | 140 |
| 8 | 160 | 165 |

This is a measured improvement, not proof of sustained 60 Hz or full-route
performance. Input, actor scheduling, collision semantics and graphics remain
covered by their existing tests; whole-game fidelity is still incomplete.

## Vulnerability dispatch and empty weapon slots

A separate four-byte-per-definition `actor_vulnerable` table now selects the
existing native vulnerability callback. It preserves the eight-byte render
descriptor and its cheap indexing. Inactive actors return before any metadata
lookup. Non-target actor kinds, hidden walls and eruptions retain their previous
special cases; all other family callbacks keep the original precedence. The
linked-table test compares all 66 entries against the prior family lookup rules.

The skeleton weapon update pass returns a 24-slot bitmask of loaded, active
weapons. Player-contact checks visit those slots in the same ascending order,
after all weapon movement. This avoids calls for inactive slots without a
second pool scan or persistent bookkeeping. Existing source traces still check
movement and retirement; a boundary fixture covers slots 0, 7, 15 and 23 plus
a retired slot with stale animation state.

Against the packaged 0421c01 cartridge, the same 180-frame entry benchmark gives:

| Round | Previous updates | New updates | Previous median game cost | New median game cost |
|---|---:|---:|---:|---:|
| 1 | 151 | 167 | 490 | 460 |
| 2 | 175 | 176 | 435 | 425 |
| 3 | 118 | 131 | 695 | 625 |
| 4 | 147 | 160 | 615 | 535 |
| 5 | 167 | 172 | 515 | 485 |
| 6 | 124 | 135 | 685 | 615 |
| 7 | 141 | 155 | 640 | 535 |
| 8 | 163 | 164 | 595 | 525 |

Costs are SGDK subticks (76,800 per second), excluding rendering, audio and
VBlank processing. These are entry-route measurements with injected
invulnerability, not sustained full-game performance or a fixed-state CPU
microbenchmark. Projectile pool scanning, rendering and frame overruns remain.

## Shared actor edge integration

Fixed 3351 performs medium-actor X integration, possible retirement, then Y
integration and its own possible retirement. High-byte-zero coordinates survive.
Otherwise the wrapped low byte minus 48 must be at least 161 for X or 160 for Y.
Fixed 3614 bypasses retirement when actor mode bit 4 is set; 361B clears active
and toggles the active persistence bit. Native `actor_motion` reuses the existing
axis predicate, applies this order, and clears the active persistence bit while
preserving consumed state. Supported caller states use active/consumed values
1/3, matching the source XOR transition to 0/2.

The helper now serves the three skeleton variants and the bank-2 wandering wisp.
Their constructors use mode 08; current native transitions do not set retirement
suppression. They bypass the earlier broad pre-movement distance cutoff. A wisp
retired by motion no longer proceeds to player contact. Other families retain
their existing handlers until their dynamic mode rules are established.

The development oracle executes original 3351 directly with valid actor and
display records, disabled player contact and zero camera delta. It covers 696
axis/boundary/velocity/mode/persistence combinations. Host comparison repeats
them at four native camera offsets (2,784 cases), checking active state, both
coordinates and persistence. Existing 2,190 skeleton and 1,920 wisp source ticks
still match. Cartridge fixtures verify real updates retire all four definitions
at the right edge without kill rewards and preserve consumed rows. Source
category counters, global camera/scanner cadence, and wrapped sprite visibility
remain outside this integration check.
