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
