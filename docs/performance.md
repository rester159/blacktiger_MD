# v27: 40-FPS target remains unmet

The 229-case survey’s worst rolling second improves from 12 to 15 FPS, with each level’s minimum improving. Sixteen one-minute traces also expose sustained regressions around 40 FPS. See the [full report](../reports/performance-profile-v23.md), [original sustained fixtures](../reports/per-second-v27.html), [additional difficult fixtures](../reports/per-second-extra-v27.html), and [all-position survey](../reports/per-second-survey-v27.html). Fixed seconds and rolling windows are both available; scene averages do not establish the floor.

The pass reduces scrolling reloads, unused projectile scans, damage dispatch work and held-animation interpreter overhead. All 157 test commands and strict packaging pass. Level 6 keeps its original artwork and disabled parallax.

---

# v26: original level 6 scenery

Level 6 parallax is disabled and its full original scenery map restored. The temple appears once in its source location. [Per-second comparison](../reports/per-second-v26.html): the level 6 fixture’s worst rolling second falls 25 → 20 FPS, with below-30 fixed seconds increasing 1 → 4 and zero dropped ticks. Other selected scene minima are unchanged. This is the requested visual restoration, not a performance optimization.

[Full report and validation](../reports/performance-profile-v23.md).

---

# v25: second-by-second cadence and scenery

Use the [interactive 480-second comparison](../reports/per-second-v25.html), [CSV](../reports/per-second-v25.csv), and [full report](../reports/performance-profile-v23.md). Each scene has 60 fixed one-second bins plus rolling windows, with interrupted PLAY bins left blank. Scene averages do not establish a performance floor.

The cave’s worst rolling second improves 15 → 18 FPS; level 7 improves 11 → 13; level 6 improves 14 → 25. Cave seconds below 20 decline 7 → 4, but its below-30 seconds increase 23 → 25. Level 8 remains mixed. No guaranteed 30-FPS floor is claimed.

Scenery changes compile offline into native tiles/palettes. All eight original scenery palettes are retained; levels 5–7 use cleaned, retiled motifs assembled only from existing artwork. Actor palettes, platform contours and collision maps remain intact. Full validation is recorded in `reports/v25-validation.json`.

---

# v24 resumed optimization

Terrain-strip walkers, dedicated world-object dispatch, shared boss queries and smaller hot call paths raise the sustained cave encounter from 30.22 to 34.15 FPS. The eight selected scene averages now range from 31.20 to 56.07 FPS; short dips remain below those averages. Level 3's selected average regresses, while seven improve.

See [the updated performance report](../reports/performance-profile-v23.md) for all results, reproduction commands and validation. The full suite passed; 20,000 differential terrain cases preserve cache/reference behavior; the installed RetroArch core matches the cave and level-7 traces exactly. Display delivery and physical hardware remain unmeasured.

# v23 measured encounter performance

The 229-scene survey reproduces the reported dips across all eight levels. Real 68000 instruction attribution identifies weapon collisions, actor updates, spawn scanning and rendering as costly work. Batching contact geometry, direct skeleton routing and bounded wraparound spawn searches improve the measured encounters, but do not solve all severe dips. The old short entrance patrols must not be treated as whole-game performance evidence.

See [the complete v23 profile](../reports/performance-profile-v23.md) for methods, exact before/after results, regressions, limits, raw traces and reproduction commands. Eight one-minute checks supplement the map survey. Your installed RetroArch core and the profiling core produced identical traces in two comparison encounters. Host display pacing and real hardware are not measured.

# v22 palace layer composition

The v21 opaque level-8 HUD hid foreground tiles at the top and bottom. Its generic pen-15 transparency rule also removed solid palace fill, while the exterior-only sky mask left opaque navy tiles across the open area between halls. Those were composition errors; scrolling-rate checks alone did not detect them.

Level 8 now preserves the source palace fill and treats only the exact navy sky color as transparent, including alternate/hidden tile variants. Complete source landscape tiles move to the far layer; the broad exterior color mask and the warm-pixel bridge mask are removed. Columns, platforms and wall details stay in the foreground. The original transparent HUD glyphs expose the actual map underneath; there is no opaque HUD band. Distant scenery continues to move horizontally at half foreground speed.

`palace-composition-runtime-tests.json` compares 1,413,707 architecture pixels across the whole map to the original pre-mask artwork. Five viewport fixtures cover the reported open area, ground and palace halls. Live-pixel checks verify transparent HUD composition and half-speed scenery in both open-air fixtures, alongside exact resident terrain checks. This is stronger than treating an opaque, motionless HUD as a successful fix. Full natural playthrough and hardware validation remain separate.

# v21 palace and Debug corrections

Palace columns now remain in the original terrain artwork, at exactly foreground speed. The former 1.25-speed sprite columns and the wall patches used to erase their original locations are removed. This fixes attachment, sprite-load disappearance and damaged torch artwork, and frees decorative sprite bandwidth. Only the distant scenery scrolls at half speed. Whole source landscape tiles are masked before color-based boundary masks, preserving architecture while removing warm-colored foreground debris. Source transparent pixels are respected in level 8, including hidden and bonus patches.

The level-8 HUD uses the sky-filled opaque glyph path, so terrain cannot obscure its top/bottom bands. Palette conversion runs only for changed HUD rows. Its solid fill uses reserved tile 1011, outside the NPC dialogue font and terrain/far-plane allocations. The native final-dragon adapter keeps its full 64-pixel body above the actual solid floor at world Y 256. Source attack scripts remain unchanged; attack/damage/clear tests still apply.

Infinite Zenny is a fifth Debug switch, default YES. It maintains 65,535 at simulation boundaries and during purchases, avoiding both depletion and reward overflow. Switching it off restores normal charges, and normal Play clears the Debug session. `reports/palace-debug-runtime-tests.json` exercises both settings, purchases, normal Play and the reported dragon descent. Column motion is checked in normal level 8 and Boss Rush by `reports/arena-parallax-runtime-tests.json`.

# v20 scenery and menu corrections

Source transparency is applied before palette quantization in levels 5–7. Mountain, sky and stained-glass decoration is classified by original tile code; collidable tiles are never removed as distant scenery. The prior window rectangle/color heuristic could erase platform edges, while palette-based sky masking fragmented architecture and clouds. Level 5 now uses the existing half-speed background scroll path. Level 6 retains the complete source citadel and distant islands; its original red spike platforms and purple platforms are preserved.

HUD variants reuse existing tile slots. Their opaque background prevents overhead terrain from obscuring the readout; level 6 uses sky-colored fill with contrasting lettering. HUD bank selection is a constant-time ROM lookup. There are no new per-frame scenery sprites, large RAM buffers or gameplay timing changes. All menu families, including the shop, use an inset Yashichi cursor.

`reports/scenery-fixes-runtime-tests.json` checks unchanged HUD pixels during camera motion, sky fill, resident terrain and cursor gutters. `reports/backdrop-runtime-tests.json` now includes level 5’s 2:1 foreground/background motion. The level-5 reported edge joins the existing controller-driven wrap cases. These are fixture-based checks, not complete level playthroughs.

# v19 horizontal map wraparound

The original tile addressing repeats at the horizontal map width. The port had
instead returned solid collision outside the map, clamped player X, and clamped
the camera. Those artificial limits blocked the reported joins in levels 2, 3
and 4. The earlier v18 explanation that level 2's right edge was intentionally
closed was incorrect; going left was an alternative route, not proof of a wall.

Normal gameplay now keeps player/camera movement continuous across the join.
Collision and terrain tiles mask X to the map width. Source spawn rows are
translated into the nearby visible lap, including rows on the opposite edge;
animated terrain and hidden patches use that same repeated map. Actor persistence
is retained. Bonus entrances work in repeated laps. Boss Rush retains its arena
bounds. No level reload or position teleport is needed when crossing a join.

The supplied Yashichi cursor retains its white/gray blades and uses stronger red
pens for its warm-colored body, without changing the title palette.

Validation in `reports/horizontal-wrap-runtime-tests.json` includes both directions
on six levels, exact resident terrain pixels, continuous camera movement, no
reload, the three reported platforms, and native spawns across the join. Fixture
starting positions are injected; movement thereafter uses ordinary controls.
This is not a full playthrough or hardware validation. The complete release checks
are recorded in `reports/v19-validation.json`. The restart fixture waits for an
in-flight reward tick to finish before injecting death resources. Profiling
also interprets wrapped negative camera coordinates correctly when counting
visible actors.

# v18 Yashichi cursor and direct Debug level starts

The supplied `art/yashichi.png` provides a 16×16 selection sprite throughout Home,
Options and Debug. The asset compiler samples the original pixel grid and maps it
into the existing title palette; the title artwork and palette are unchanged.
Arcade and the initial mode picker retain their original arrow. The cursor uses
one sprite, updated only when the menu changes, with no gameplay rendering cost.

Debug now shows all four switches and all eight levels together in two columns.
The switches remain ON by default. Highlight a level and press A or Start to begin
immediately with the chosen Debug settings. Up/down traverses each column; left
or right moves to the corresponding item in the other column. B returns to Home.
There is no intermediate level-selection screen. Normal Play remains unchanged.

The reported level-2 shopkeeper at (640, 928) had its 32-pixel body origin on
an ice platform face. NPC spawning now raises a body by 32 pixels only when its
origin intersects solid terrain and both cells above are open. This moves the
shopkeeper and rescue contact together to (640, 896). Other sampled source NPC
placements do not meet this correction condition. A regression rescues him through
normal controller input and verifies that the shop opens.

The reported right-hand ledge is the map boundary, not a blocked exit. A cartridge
regression starts at (1992, 528), jumps left, climbs the nearby poles, and reaches
x=1780 using only controller input after setup. No wall or scenery was removed.
This verifies leaving that ledge, not a full playthrough of the level.

Validation is recorded in `reports/v18-validation.json`; current frame timing is
in the versioned v18 pacing reports. No rendering scheduler or gameplay AI changes
were made in this update. The wave-boss runtime check now allows two refreshes
for the in-flight final damage tick to finish before checking its reward: the
previous immediate read could see life reach zero before the score write.

# v17 full-size menus and explicit Debug controls

Home uses two columns: Play / Boss Rush on the left, Options / Debug on the right.
All menu lettering and Capcom/Rester footers use the original 8-pixel size. Options,
Debug, and the eight-level selector also use two columns. The original logo and
SEGA chant remain intact.

Home Play starts a normal game from level one, without level selection or Debug
effects. Boss Rush and Arcade also retain normal rules. Home → Debug contains
independent Invincibility, Infinite Lives, Infinite Time and Framerate switches,
plus Select Level. All four default ON for exploration, retain their choices between
runs, and apply only to runs started from Debug's level selector. Invincibility
blocks damage, lethal hazards, poison and reversed controls. Bottomless falls
recover at a checkpoint. Infinite Lives preserves the life count on death even
when invincibility is OFF. Infinite Time freezes the countdown independently.
Framerate displays actual presentations per second in the upper-right HUD, sampled
once per second against the video refresh clock (60 Hz NTSC / 50 Hz PAL). It does
not report simulation ticks or the emulator host FPS. The counter updates only
when its displayed value changes and is absent from normal Play.

An active Debug session reapplies its invincibility setting on every game update,
so protection does not depend solely on the initial player-state assignment. Tests
clear that player flag in all eight levels and verify its restoration. New game
startup clears the active Debug session before applying the chosen launch mode.
The Debug test covers all eight switch combinations, including real projectile
contacts, death/respawn with finite/infinite lives, timer behavior, and normal Play
reset. Controller toggles and HUD tile checks verify Framerate ON/OFF and its
default ON state. Poison/reversal tests verify that protection does not consume antidotes.

The launcher opens a decorated 960×720 window and disables automatic save-state
loading for this launch, without saving these overrides to global configuration.
The v16 graphics scheduling improvements and scenery are retained. Validation and
current performance are recorded in `reports/v17-validation.json` and the versioned
v17 pacing reports. Emulator patrols are not complete playthroughs or hardware tests.

# v16 pipelined gameplay and presentation

The NTSC renderer now publishes a completed graphics queue to a VBlank interrupt,
then uses the time before that interrupt to prepare one gameplay tick for the
following frame. The next loop credits that prepared tick against elapsed time.
This removes much of the old wait/catch-up cycle: a late frame no longer forces
all of the next simulation work to start after the next presentation.

Only a fully built, immutable DMA/SAT/scroll queue is handed to the interrupt.
Gameplay preparation does not call the renderer; the main loop waits for the
submission to finish before modifying any rendering buffers. Compiler barriers
protect that ownership handoff. Scene changes are rendered on the next loop.
Preparation plus ordinary catch-up stays bounded to three ticks per iteration.
Menus, transitions, and PAL retain synchronous submission. Audio follows the
submission and retains its refresh clock and queued sound commands.

The VBlank callback records the graphics deadline after DMA, scrolling and palette
work, before controller polling. Controller polling can finish in active display
without causing a late VDP write. Previously the metric included this polling.
Both early synchronous and interrupt-owned submissions use the graphics deadline.

The scenery, parallax, sprite graphics and enemy simulation remain unchanged.
No sprite interpolation, reduced AI rate, scenery removal or speculative animation
upload is needed for this improvement. The timing gain comes from doing useful
simulation work while a completed picture waits for its display deadline.

Home Level Select now enables exploration: ordinary damage and lethal hazard
immunity, a frozen countdown, and checkpoint recovery without life loss after a
bottomless fall. The hero remains visible instead of continuously flashing.
Starting a fresh Arcade or Boss Rush game clears exploration. The level-selection
screen identifies the mode with “INVINCIBLE / TIMER OFF”. Regression and performance
fixtures explicitly disable exploration when testing normal damage/timer behavior;
controller-only level-selection tests cover the enabled mode in all eight levels.

One-minute Genesis Plus GX patrols (3,600 NTSC refreshes), with normal countdown
and the same temporary damage shield used for the v15 baseline:

| Sample | v15 draws/s | v16 draws/s | Repeated refreshes, v15 → v16 | Worst v16 one-second draw count |
| --- | ---: | ---: | ---: | ---: |
| cave_middle | 30.12 | 56.63 | 1793 → 202 | 42 |
| palace_upper | 31.85 | 59.00 | 1689 → 60 | 59 |
| palace_lower | 59.40 | 59.28 | 36 → 43 | 59 |

Each sample executes exactly 3,600 gameplay ticks, with no discarded ticks,
no late graphics writes and no draw interval beyond two refreshes. Captured
playfield pixels change 3,397 / 3,540 / 3,557 times, independently corroborating
the presentation counters. Lower palace remains near its earlier rate; crowded
cave and upper palace gain substantially. Cave still has occasional uneven pacing,
including a worst one-second window of 42 draws, so this is not a locked-60 claim.

With actual Level Select exploration enabled (no temporary flashing shield),
the corresponding results are 57.73 / 59.97 / 60.00 draws/s, with a completely
frozen countdown. Enemy AI continues normally in both sets of samples. Scene
details vary slightly with controller sampling and presentation timing. These
patrols do not establish full-route, physical-console, or PAL performance.

Evidence: `reports/frame-pacing-v15-extended.json`,
`reports/frame-pacing-v16.json`, `reports/frame-pacing-v16-extended.json`, and
`reports/frame-pacing-v16-exploration.json`. The regression thresholds now guard
the improved cave/palace cadence and independently observed image changes.

Cartridge SHA-256: `15724d07c9340e8fbb735448163c8b972dbb26dc30ab8782d3db208f8ef83351`.

Validation: see `reports/v16-validation.json`. Controlled runtime fixtures now
pause before sensitive RAM injections, allow camera reloads to finish before
checking contacts, and keep weak-point projectile fixtures out of solid terrain.
The flailer recoil check still uses the chain; the lethal body hit uses a narrower
dagger so a newly launched flail does not intercept it. Source behavior oracles
and expected damage/reward outcomes are unchanged.

# v15 crowded-scene CPU work and presentation deadlines

This is a modest improvement, not a 60-fps fix for crowded cave/palace encounters.
Scenery, fixed gameplay steps, enemy routines, and the v14 menu/audio features are
retained. Common wisps, crawlers and zombies take a shorter dispatcher path;
contact tests reject separated actors on X before computing Y; dormant hidden
objects avoid unused contact/patch lookups. Sprite body cache misses and DMA
assembly are separated from the common cached draw path.

FM register writes now run immediately after presentation. Previously a burst
could hold an already prepared graphics queue past its blanking deadline. The
music clock and queued game events are preserved. The late-VBlank transfer margin
and fixed-tick scheduler are unchanged. Rendering-skipping/recovery experiments
were rejected because they worsened frame spacing.

The ten-second upper-palace sample improves from 30.6 to 34.9 presentations per
second. Sustained one-minute patrols give the more conservative comparison below:

| Sample | v14 presentations/s | v15 presentations/s | Refreshes without a new draw, v14 → v15 | Longest v15 interval, refreshes |
| --- | ---: | ---: | ---: | ---: |
| cave_middle | 30.03 | 30.12 | 1798 → 1793 | 2 |
| palace_upper | 30.25 | 31.85 | 1785 → 1689 | 2 |
| palace_lower | 58.67 | 59.40 | 80 → 36 | 2 |

All three one-minute samples execute 3,600 simulation ticks in 3,600 refreshes,
with no discarded ticks, late-VBlank overruns, or presentation gap beyond two
refreshes. The cave gain is negligible; the crowded scene remains near 30 fps.
Upper palace still spends much of the sustained encounter at 30 fps. Lower palace
has 55% fewer repeated refreshes (80 down to 36), averaging 59.4 presentations/s.
These are deterministic Genesis Plus GX patrols with real AI and invulnerability;
the encounter details can vary slightly with presentation timing. They do not
prove a natural full playthrough, PAL behavior, or physical-console performance.

`tests/test_frame_pacing.py` now checks presentation intervals and the one-minute
crowded samples in addition to the thirteen short samples. Packaging requires the
extended report to match the ROM hash. Reproduce one scene with:

```sh
.venv/bin/python tools/profile_pacing.py --frames 3600 --scene palace_upper --output .local/palace-pacing.json
```

All 144 regression commands passed; see `reports/v15-validation.json`.

Cartridge SHA-256: `c694dfb0a97d039b5988b2034fbd0b7e11e7faaa9f16fc0de598a406d7216ca0`.

Evidence: `reports/frame-pacing-v14.json`, `reports/frame-pacing-v14-extended.json`,
`reports/frame-pacing.json`, and `reports/frame-pacing-extended.json`.

# v14 scenery-preserving performance and readable menus

The fixed gameplay clock and all decorative backgrounds are retained. The main
measured gains are cave entry (50.7 to 58.6 presentations per second) and lower
palace (50.3 to 58.8). Crowded cave and upper-palace patrols remain near 30;
this is a partial smoothness improvement, not a locked-60 fix for those encounters.

Terrain bounds/stride are cached per scene, boss-family checks use a generated
classification table, and native actor paths avoid unused coordinate conversion.
Body sprites now share the direct key index with piece sprites, using tagged
entries and explicit invalidation instead of scanning twenty body-cache slots.
The expensive diagnostic clocks sample one iteration per sixteen presentations;
`profile_samples` identifies completed samples for the profiling tools. These
cost estimates are separate from the per-refresh simulation/presentation counters.
No AI updates, animation steps, or decorative layers were removed.

Menu options and the Capcom/Rester footers now use seven-pixel cells, the closest
crisp whole-pixel size to the requested 10% reduction from eight pixels (12.5%
actual reduction). The second menu no longer repeats Arcade or Home. The SEGA
chant and clean logo skips are preserved. See `screenshots/menu-v14-review.png`.

Same 600-refresh NTSC patrol recipe in Genesis Plus GX; encounters can vary
slightly with presentation timing. Numbers are game presentations per second,
not the emulator's 60 Hz output counter.

| Sample | v13 presentations | v14 presentations | v14 simulation ticks |
| --- | ---: | ---: | ---: |
| level1_entry | 60.0 | 59.1 | 60.0 |
| level2_entry | 60.0 | 60.0 | 60.0 |
| level3_entry | 58.7 | 60.0 | 60.0 |
| level4_entry | 50.7 | 58.6 | 60.0 |
| level5_entry | 59.1 | 60.0 | 60.0 |
| level6_entry | 54.6 | 59.6 | 60.0 |
| level7_entry | 45.0 | 58.6 | 60.0 |
| level8_entry | 52.5 | 58.4 | 60.0 |
| cave_middle | 29.9 | 30.2 | 60.0 |
| windows_middle | 56.8 | 59.8 | 60.0 |
| palace_upper | 30.0 | 30.6 | 60.0 |
| palace_lower | 50.3 | 58.8 | 60.0 |

Every continuous-play sample advances 600 simulation ticks across 600 refreshes,
with no discarded ticks or measured late-VBlank overrun. The sky route exits PLAY
for a rescue and is excluded from that clock assertion. Lower palace has a new
570/600-presentation regression floor. Source-derived actor routing, sprite pixels,
scrolling, boot audio, and the full cartridge regression recipe are checked.
Natural full routes, PAL and physical hardware remain outside this measurement.

All 144 regression commands passed; see `reports/v14-validation.json`.

Cartridge SHA-256: `44fd7033384e834899de2ed57cdbe785f705c3a4d63a6460c963ae322e7ffeb7`.

Evidence: `reports/frame-pacing-v13.json`, `reports/frame-pacing.json`, and the
runtime reports for the packaged ROM. Run `make test`, then
`.venv/bin/python tools/package.py --name blacktiger_MD_v14.bin`.

# v13 smoothness, boot audio and menus

v13 preserves v12's fixed gameplay clock and improves actual presentation cadence.
The SEGA logo now plays the supplied Sonic 1 chant (signed 8-bit PCM, 16 kHz,
102 audible NTSC refreshes). Both logo skips stop audio before the title.
Selectable menu labels and values use 6×6 glyphs with six-pixel spacing, exactly
75% of the original 8×8 font. Headings, prompts and in-game HUD retain their size.

A runtime audio check exposed a GCC 16 m68k optimization defect in SGDK's Z80
upload loop: the generated instruction incremented the source address before
using that same register to calculate the destination. Driver bytes arrived one
byte late. The PCM command never ran, and the idle driver's shifted jump sent the
Z80 into banked cartridge memory (PC `0xf343` observed in v12). Project-local
assembly uploads now use separate address registers for PCM and idle drivers.
Tests check their actual Z80 RAM bytes, non-silent chant duration, FM jingle,
and silent tails after skipping. The global compiler settings remain unchanged.

Rendering changes precompute cave-border horizontal geometry, batch consecutive
terrain patterns and fragmented enemy body patterns into fewer DMA requests,
and cull invisible actor art before family-specific frame selection. A late
VBlank submission budgets both queued bytes and setup operations, with a
conservative margin for scroll/input processing. No measured overrun occurred.
To fit the chant inside the 4 MiB cartridge, identical 2 KiB sprite-atlas blocks
are shared losslessly and the unused original palace atlas is omitted from ROM.
The canonical atlas and original palace data remain available for pixel tests.

Same 600-refresh NTSC patrol recipe as v12, measured in Genesis Plus GX. Counts
below are displayed presentations and simulation ticks per 60 refreshes, not the
emulator's output-refresh counter. Encounter details can vary with update timing.

| Sample | v12 presentations | v13 presentations | v13 simulation ticks |
| --- | ---: | ---: | ---: |
| level1_entry | 59.1 | 60.0 | 60.0 |
| level2_entry | 59.9 | 60.0 | 60.0 |
| level3_entry | 57.1 | 58.7 | 60.0 |
| level4_entry | 43.0 | 50.7 | 60.0 |
| level5_entry | 59.7 | 59.1 | 60.0 |
| level6_entry | 50.8 | 54.6 | 60.0 |
| level7_entry | 36.1 | 45.0 | 60.0 |
| level8_entry | 48.5 | 52.5 | 60.0 |
| cave_middle | 28.3 | 29.9 | 59.9 |
| windows_middle | 56.5 | 56.8 | 60.0 |
| palace_upper | 29.1 | 30.0 | 60.0 |
| palace_lower | 46.3 | 50.3 | 60.0 |

All twelve continuous-play samples retain 599–600 simulation ticks per 600
refreshes, no discarded ticks and no late-VBlank overrun. The sky patrol exits
PLAY for a rescue, so it is excluded from that clock assertion. The crowded
cave and upper palace still present roughly 30 frames per second; this build
improves smoothness without claiming locked 60 fps everywhere. Natural full routes,
PAL output and physical hardware remain separate validation work.

The 144 commands in the regression recipe passed against ROM SHA-256
`ab8ffdfdc3d7b0b1d5319784f26b16bba4bb0e54e87e776ad23992d85dfc337e`.

Evidence: `reports/frame-pacing-v12.json`, `reports/frame-pacing.json`,
`reports/boot-logos-runtime-tests.json`, and `screenshots/menu-v13-review.png`.
Run `make test`, then `.venv/bin/python tools/package.py --name blacktiger_MD_v13.bin`.

# v12 gameplay clock and presentation timing

The v11 loop advanced the simulation once per rendered frame. A missed refresh
therefore permanently lost a gameplay tick: movement, AI, attacks and the game
timer all slowed down with rendering load. An emulator's refresh-rate display
cannot detect this distinction.

Gameplay now consumes elapsed video refreshes as fixed simulation ticks before
rendering. Every catch-up tick executes the original movement, AI and collision
code; physics deltas are unchanged. Each iteration processes at most three
refreshes and retains a small remaining debt. Backlogs beyond six refreshes
(about 100 ms) are clamped and counted. Mode changes, round changes and full
terrain reloads reset the clock anchor so loading time is not replayed as gameplay.
Held input retains its single press edge; native sound commands accumulate until
the once-per-presentation audio update. PAL retains the 6:5 tick conversion but
has not been validated in the emulator.

The cave HUD's scrolling right edge previously rebuilt 64 pixel rows with variable
32-bit shifts on the 68000. Its 256 exact offsets are now generated offline
(about 15 KiB of deduplicated ROM data), assembled with plain memory copies,
and sent in one transfer. The pixel regression checks every
offset against the original texture, including non-tile-aligned positions.

Terrain scrolling now updates up to two exposed tile rows/columns incrementally.
A catch-up fall can cross more than one row; previously that triggered a full
level-art reload. Eight-level VRAM checks cover 80 multi-tile scrolls in both
axes without a reload or cache fault.

## Measured clock speed versus visible presentation

These are 600-refresh NTSC patrol samples (about ten seconds), with real enemy AI
and an invulnerable player. Only uninterrupted PLAY samples appear here. Enemy
counts, per-refresh simulation steps, game-timer steps and presentations are in
`reports/frame-pacing-before.json` and `reports/frame-pacing.json`. Inputs alternate
left/right every 30 simulation ticks; neither run edits RAM during measurement.

| Scene | v11 game ticks/s | New game ticks/s | New presentations/s |
| --- | ---: | ---: | ---: |
| level1_entry | 59.0 | 60.0 | 59.1 |
| level2_entry | 59.9 | 60.0 | 59.9 |
| level3_entry | 56.9 | 60.0 | 57.1 |
| level4_entry | 48.6 | 60.0 | 43.0 |
| level5_entry | 59.0 | 60.0 | 59.7 |
| level6_entry | 50.4 | 60.0 | 50.8 |
| level7_entry | 48.1 | 60.0 | 36.1 |
| level8_entry | 52.3 | 60.0 | 48.5 |
| cave_middle | 33.2 | 60.0 | 28.3 |
| windows_middle | 53.2 | 60.0 | 56.5 |
| palace_upper | 46.5 | 60.0 | 29.1 |
| palace_lower | 49.5 | 60.0 | 46.3 |

The simulation and game timer stay within one tick of real time in these twelve
samples, with no discarded ticks. Every rolling 60-refresh window contains at
least 58 simulation ticks. The sky-middle patrol changes mode and is reported
separately; it is excluded from the uninterrupted-play assertion.

This fixes the measured slow-motion effect, but does **not** establish smooth
60-picture-per-second rendering. Catch-up can reduce presentation rate in busy
scenes because it spends CPU time on previously lost simulation work. The cave
and upper palace still repeat pictures, as the last column makes explicit.
Full natural routes and real hardware remain unverified.

`make test` includes clock/timer drift assertions, one presentation per refresh,
bounded exceptional stalls, held Start/pause behavior, boss traversal and pixel
checks. A performance report's cache/blanking `passed` field alone is not a
smoothness guarantee. Package a named tested ROM with
`.venv/bin/python tools/package.py --name blacktiger_MD_v12.bin`.

The following table is historical: it predates the fixed gameplay clock and
compares the earlier renderer change using v11's matching ROM hash.

# Earlier rendering optimization results

Measured with Genesis Plus GX in 17 deterministic NTSC samples. Each sample spans 600 video frames (approximately ten seconds). Update counts include intervening game modes, so these are comparative load samples, not continuous-play FPS guarantees. No natural full playthrough or hardware validation is claimed.

| Scene | Before updates | After updates |
| --- | ---: | ---: |
| level1_entry | 592 | 590 |
| level2_entry | 594 | 596 |
| level3_entry | 528 | 533 |
| level4_entry | 548 | 559 |
| level5_entry | 589 | 587 |
| level6_entry | 487 | 487 |
| level7_entry | 545 | 545 |
| level8_entry | 570 | 573 |
| cave_middle | 420 | 467 |
| sky_middle | 474 | 539 |
| windows_middle | 470 | 472 |
| palace_upper | 331 | 453 |
| palace_lower | 436 | 521 |
| palace_blue | 594 | 594 |
| rush1 | 588 | 594 |
| rush5 | 576 | 598 |
| rush8 | 343 | 589 |

Shared changes apply to every level: losslessly repacked actor graphics, fewer DMA requests for 32×32 bodies, unrolled sprite scanline-budget checks, and a bounded 2 KiB late-VBlank submission window. Large bosses use one 32×32 hardware sprite per four original cells. Cave HUD scenery caches its geometry, and palace columns share a single conservative capacity check. Actor artwork, palettes, movement and AI are unchanged.

Level 8 windows and exposed blue scenery now share a resident half-speed landscape. Foreground columns retain their separate speed. The pixel test checks a 16-pixel camera move produces 8-pixel scenery motion.

All 17 samples recorded zero terrain-cache faults and zero VBlank overruns. The full regression suite passed. Additional tests compare five large-boss profiles in both facings against canonical source-cell geometry and actual VRAM pixels.

Some scenes remain below 60 updates per second, especially crowded Level 3/4/6/7 sections and the upper palace. Near-full-rate entry scenes show little change, and small differences of a few updates should not be treated as meaningful gains.

Reproduce with `make test`, then `.venv/bin/python tools/package.py`. `tools/profile_all_levels.py` accepts `--rom`, `--symbols`, and `--output` for comparison against an older matching ROM/symbol pair.
