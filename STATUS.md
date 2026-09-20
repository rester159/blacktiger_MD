# Status

Deliverable: an SGDK development cartridge and a reproducible new repository.
User's requested complete native Black Tiger port: **not achieved**.

The most important next work is source-derived actor/constructor coverage, not implementing another
round-specific runtime. The eight maps already use one renderer and game loop. Replace the remaining provisional
actor family behavior in `tools/extract.py` and `src/game.c` with verified animation,
attack, hitbox, reward, and transition data. In particular, do not count the current boss assignments
or injected ending test as proof that any round is naturally completable.

Known native issues: frame overruns on denser routes; unverified PAL timing; placeholder audio;
provisional player and shop rules. Exact cadence, cartridge hash, and test counts live in the JSON
reports and `dist/build.json`.

Resolved during this build: wrong-CPU libgcc, sprite-cache lookup cost, full-view cache pinning cost,
repeated HUD formatting cost, disappearing/stale background tiles caused by DMA queue overflow,
hero/font palette interference, redraw batching on large camera changes, and a GCC 16 optimization that widened the loot RNG
high-byte read into a 68000-invalid odd-address longword read (now an explicit volatile word load).

Verified progress: the common actor animation loader is now a native typed routine with original-ROM
trace comparisons. All eight petrified NPC variants use source-derived constructors, idle frames,
rescue visuals, and distinct reward dispatch; actual-cartridge tests cover their persistence.
This does not validate other actor families, hint text, complete cutscene timing, or shop economics.

Remaining work order (shared systems, not sequential levels):
1. Extend the witnessed constructor census to dynamic branches and complete actor/boss definitions.
2. Implement source-derived player/combat, enemy families, containers, drops, and boss composition.
3. Match progression, shops, score, equipment, cutscenes, and natural round completion.
4. Replace placeholder audio, match presentation/palette behavior, and meet frame budgets.
5. Validate natural full-game routes and PAL/NTSC behavior; package only the tested cartridge.

Constructor census now witnesses copies for all 66 known definitions under four RAM profiles.
The adjacent-code template scan and 5/8-byte frame heuristic have been removed. Linked-ROM checks
verify initial health for 65 definitions and initial graphics for 51. The other values are explicit
fallbacks, and none of this proves later AI behavior. Two data-selected objects remain incorrectly
labeled rocks and need their own state handling. Compound boss constructors copy 96/192 bytes,
confirming that one generic actor body is insufficient.

The twelve invisible background-breakable definitions are now a distinct stationary native family.
All 39 source locations share sparse collision/map patches, source reveal and explosion clips,
five-hit opening, persistent open/collected state across camera despawns, and the twelve reward
handlers. The host tests check all cells under 55 patch combinations; cartridge tests check all 39
rows, live VDP pixels, hits and rewards. Original MAME checks independently exercise 39 patch writes
and 12 reward dispatches. Weapon/contact bounds, maximum-HP progression, screen-attack enemy
selection and persistence across death still need broader arcade matching.

Three skeleton variants (source constructors 93ED/9B85/A35C) now share a native C transition
routine and source-compiled animation segments. Durability is 12/36/48 rather than the one-point
callback trigger; shield variants block directionally. Walking, approach/swing, separate weapon
actors, obstacle jumps, falling, damage, persistence and death match 2,190 original-ROM ticks across
30 controlled scenarios, plus 822 weapon frame comparisons. Cartridge tests cover each actual
source constructor, nonfatal/fatal projectiles, shields, score, and retirement. Normal body contact now uses source dimensions; weapon hitboxes, alternate posture, and player damage rules remain provisional.

The common death-drop system now uses all 28 source selection tables, seven coin values, the source
random recurrence, and pickup animations. Original-ROM comparisons cover 896 selections, 1,687
animation ticks, seven rewards, full-pool refusal and 448 random updates. Cartridge checks cover
three actual skeleton death callbacks, collection and expiry. Native loot currently has its own
33-slot pool; source competition with other small actors, exact random update phase and player
contact bounds remain gaps. Remaining enemy families and compound bosses are still required.

The stationary directional actor (bank 2 constructor B67F, 24 source placements) now uses its
source facing/blink cycles and death sequence instead of firing generic turret projectiles.
The reusable 32-direction aiming routine matches 512 original-ROM observations; eight controlled
actor scenarios match 1,440 ticks, including nonfatal/fatal damage and persistence. A linked-ROM
check covers a real spawn, stationary behavior, absence of placeholder shots, score and retirement.
Contact geometry remains provisional. These tests do not establish a natural full-game route.

The 72 stationary lethal-zone placements (bank 1 B2A9) now use source normal-player contact
dimensions and enter death directly, bypassing armor and hurt invulnerability. Boundary checks
match 126 original-ROM cases; cartridge checks cover weapon immunity, fatal contact, interrupted
post-death interactions and single-life respawn. Alternate player contact postures and the original
death presentation/timing remain unfinished.

Placed time-extension and screen-attack pickups (58 source placements) now give their distinct
rewards instead of flat coins/score, use normal source contact bounds, persist after collection,
and retire on the following tick. The placed and hidden screen-attack rewards share the source
small/medium actor target filters, compiled from witnessed constructor pool/contact fields.
Checks cover 406 item ticks, 192 original target cases, 66 compiled definition filters, and both
actual cartridge pickup spawns. Unported enemy death callbacks, later contact-type changes and
shared-pool/projectile effects remain incomplete; this is not full screen-attack fidelity.

The renderer now packs four-piece bodies into one 32×32 hardware sprite, sharing the existing
320 sprite tiles with small objects and retaining per-frame cache pinning. Forty-eight paused
fixtures retain identical pixels, while direct VRAM checks validate mixed cache textures and
hardware scanline limits. Sprite construction cost in those fixtures falls by 47.7%; a crowded
case no longer drops a visible piece due to the old conservative band count. The slowest sampled
route improves from 129 to 149 logic updates per 180 video frames; three additional sampled
rounds reach 180/180. Other routes still overrun, and worst-case/PAL performance remains unproven.
See `reports/renderer-performance.json` for the exact scope and before/after cartridge hashes.

The two emerge/hide variants (bank 2 8000/81A2, 32 placements) now share source-compiled animation
phases, 4/16 health, 50/100 scores, exposed-only projectile collision, alternate-frame contact,
contact-extended exposure, hide/reappearance gates, and permanent death rewards. Checks compare
1,200 original actor ticks and 672 constructor attempts, including byte-wrapped proximity
boundaries. Cartridge tests cover both real spawns, early immunity, exposed hits, fatal hits,
and normal reappearance. Exact source scanner scheduling and player hurt timing remain gaps.
Renderer fixtures initialize these actors' first source frame and retain their unflipped source
orientation; reference pixels were regenerated from the pinned pre-optimization cartridge.

The wandering actor at bank 2 A6F8 (26 placements) now uses a native proximity/random movement
routine and source animation segments instead of stationary turret shots. Hits reset its cycle
and restore its one-point trigger without killing it or awarding score. Eight scenarios match
1,920 original ticks for graphics, motion, repeated hits and proximity changes. A cartridge test
covers an actual spawn, motion, absent placeholder shots and repeated nonlethal hit callbacks.
Player damage details and common viewport retirement still need broader source matching.

Small and medium actors now share source-derived normal contact geometry compiled from witnessed
constructor dimensions and pool identity. The two pools use different player origins, with inclusive
edges and player half sizes 3/8. Host-native C matches 588 original-ROM boundary observations across
12 shapes; linked-cartridge checks verify the compiled tables. All existing cartridge regressions
pass, including NPC rescue contact. Hidden-wall rewards retain their separate provisional box;
large/profile-dependent actors, alternate posture, dynamic bounds and contact scheduling still need
source matching. This does not establish complete combat fidelity.

Ordinary player damage now uses source constructor attack strength (+0F), consumes armor before
health, carries excess damage into health, and grants 60 ticks of protection on surviving hits.
Exact armor depletion does not damage health; lethal overflow enters death. The old unconditional
one-point loss and artificial upward velocity/climb cancellation are removed. Native C matches
180 original-ROM cases, and six linked-cartridge projectile cases cover absorption, overflow,
lethal damage and invulnerability. Special contact effects, source armor-break visuals, skeleton
weapon attack strength, and full player/death animation still need separate implementation.

Skeleton weapon contact now uses witnessed small-actor dimensions (8/4 half sizes), inclusive
player bounds and the source weapon damage value, replacing the oversized generic box. All three
weapon templates are verified at their actual copy instructions and against observed weapon RAM.
Checks retain 2,190 body ticks and 822 weapon frames, and add 147 native boundary cases plus 15
linked-cartridge edge cases. Variant 1's special contact type 42 is recorded but its additional
status effect remains unported; alternate posture and source collision scheduling remain gaps.

The recurring bank-zero walker (constructor 8000) now uses native typed animation transitions
for emergence, vulnerable walking, obstacle turns, fractional falling, natural disappearance and
death/drop handling. It no longer uses the generic chasing/shooting placeholder. Its constructor
counts 30 attempts, caps the family at three active actors, chooses among eight source random
horizontal positions, and searches five candidate ground heights. Death permits later spawning.
Checks compare 1,280 original behavior ticks and 1,920 constructor attempts, plus an actual cartridge
spawn through emergence, projectile death, score and recurring retirement. The port's global spawn
scanner still differs in cadence and viewport gating, and shared arcade pool contention is not
modeled. Renderer fixtures explicitly initialize its source first frame; their reference pixels
were regenerated from the pinned pre-optimization cartridge.

Player attack strength now comes from the source's five-tier attack-entry table (1/2/4/8/16)
instead of the displayed tier number. The native projectile creation path uses that lookup, and
the existing shop permits the fifth tier. Original-ROM attack-entry observations and cartridge
input/firing checks cover every tier, with an additional fifth-tier purchase check. Weapon reach,
attack poses and timing, projectile geometry and source shop pricing remain provisional.

The throwing recurring walker (bank 0 constructor 8389) now extends the shared native walker
routine with four health, one throw, repeated post-throw jumps and two death/disappearance
presentations. Its projectiles use an independent native animation pool, survive parent death,
can be destroyed by player shots, and respond to screen-clear pickups. Native comparisons cover
4,460 original body/projectile ticks including complete natural lifetimes and 1,920 constructor
attempts; cartridge checks cover real spawning, nonfatal/fatal hits, score, throwing, projectile
independence, destruction and retirement. The original walker regressions also pass.
The native missile pool has twelve dedicated entries rather than sharing the arcade small-actor
pool. Player-shot collision dimensions, global scanner cadence and viewport gating remain gaps.
The old cartridge used unrelated fallback graphics for this variant, so it is excluded from
old-pixel renderer equivalence fixtures; its actual animation frames are compared directly to
source traces and were visually checked in the emulator.

Normal small-projectile contact now uses the source's even-frame gate after movement. Dagger
hits on these projectiles use source half sizes 4/2 and the same gate, replacing the provisional
4/4 rectangle. Tests compare 196 original loader/collision cases and six linked-cartridge
one-contact-tick cases, including inclusive edges and odd/even damage differences. Chain geometry,
the source chain-hit shortcut through E906, alternate player posture, and complete weapon update
scheduling still require porting; these checks do not establish full combat fidelity.

The two stacked boss constructors (bank 4 9EB1/9F16) now preserve their two damage layers:
16 or 24 initial health, followed by 16 health after the first break. Excess damage does not carry
into the next layer. The first break neither awards a kill nor clears the round, ordinary hits
have no generic ten-tick cooldown, and final defeat awards the source 500 points without a generic
random drop. Twenty original hit-callback observations and cartridge cases for both real rows
cover nonfatal hits, exact/overkill breaks and the no-premature-clear invariant. This is a damage
progression correction, not a complete boss port: two/four-part construction, movement, vulnerable
windows, phase graphics and source death/clear timing remain unimplemented or provisional.

The main controller for both stacked bosses now uses source-compiled animation and native C
movement instead of generic chasing/shooting. The proximity vulnerability gate, weighted random
idle/toward/away/high jumps, fractional acceleration, ground bounce, wall/ceiling response,
second damage form, death animation and clear callback match 3,840 original-ROM body ticks.
Cartridge checks now require the final death animation to finish before CLEAR, and verify that
a normal projectile cannot damage the player during that sequence. Both body phases were
rendered in the emulator. Additional upper components are still absent: these bosses are not
complete, and arena setup, shared collision scheduling and the full victory presentation remain
unverified. Old generic boss images are excluded from pinned-renderer equivalence fixtures;
source animation frames have their own direct comparisons.

The stacked bosses now instantiate all two/four components. Their upper sections reuse the main
movement kernel with separate source animation graphs and random-choice weights, four damage
layers (initial 6/4 HP, then 2 HP), one-point contact damage, and independent 15-point defeat.
Main defeat forces surviving upper sections into death animations without extra rewards or
changing their main row's persistence. Boss entry clears ordinary actor/projectile pools; spawning
remains suspended during the encounter. Upper motion/damage/retirement matches 4,840 source
ticks; cartridge checks cover both compositions, independent upper defeat, and forced cleanup.
Arena gates/camera setup, the remaining boss families, and full victory presentation still require
work. These controlled checks do not establish natural round completion.

The ordinary stone enemy (bank 4 9A4C) now shares the stacked upper-component movement
kernel instead of generic walking/shooting. Its own initial animation, proximity immunity, four
two-HP damage layers, worn form, 15-point defeat, random coin drop, and persistent retirement
are native. The common movement suite now compares 7,260 source ticks including the ordinary
variant. A real round-four row passes cartridge checks for immunity, damage, drops and retirement.
This ordinary actor does not clear pools, suspend spawns, lock the player, or clear the round.

The falling boulder (bank 4 B338) now has a native proximity/fall/bounce/break routine, replacing
generic flying pursuit. The source's low-byte proximity/direction comparisons, fractional gravity,
three impacts, 50-to-2 contact damage change, 255 HP and no-drop destruction match
2,800 original-ROM ticks. Triggering the fall consumes the placement; destroying it beforehand
allows respawning. A real round-two placement passes linked-cartridge fall/bounce, dynamic contact
damage, nonfatal/fatal hit and persistence checks. Original sound effects remain placeholders.

The POW pickup now collapses remaining damage layers, matching the source's forced health/layer
writes. Simultaneously hit upper boss parts retain their pending defeat callbacks rather than
being replaced by unrewarded main-body cleanup. Source checks cover 192 target-filter/field-write
cases and both stacked compositions before/after their callbacks. Linked-cartridge collection
cases verify 15 points for an ordinary stone, 515/545 for the two stacked bosses, all layers
consumed, per-part kill counts, persistence and preservation of the death presentation.

A shared hit-handler audit corrected boulder scoring: lethal weapon/POW damage queues 300
points immediately, while natural breakage awards zero. The boulder oracle now captures the
original score task as well as body state; source and cartridge checks cover both outcomes.

Constructor bank 2 ACAC was incorrectly labeled a chest. It now creates two small flying actors
using shared native aiming/animation logic, the source spawn gate, initial immunity, random
directional movement, sixteen decision cycles and final escape movement. Each weapon defeat
awards 10 points with no guessed 50-coin chest reward. Constructor extraction now recognizes
this 64-byte pair and its dummy actor persistence pointer, providing correct one-HP, one-damage,
small-pool contact and POW eligibility. Movement/death/render frames match 58,000 source ticks
across both parts and all random selections. A real round-one spawn passes cartridge checks for
both actors, immunity, rewards and retirement. Generic player weapon rectangles and shared
small-pool contention remain unported; controlled tests do not establish natural full-game play.

Player daggers now use source small/medium actor bounds, the eight-pixel medium origin offset,
even/odd pool cadence, screen-coordinate gates and inclusive edges instead of the generic
40-by-40 rectangle. Dagger damage is half the stored attack strength, minimum one; chain shots
retain their existing behavior. Comparisons cover 1,306 original loader cases across all twelve
compiled contact shapes, including screen edges and all weapon strengths. Cartridge cases use
a dagger surviving exactly one collision tick to verify both parities, boundary hits/misses and
half damage. Chain geometry, large-actor geometry and exact weapon-state update timing remain
unported; these changes do not establish full player/combat fidelity.

The third recurring walker (bank 0 89C6) now shares the existing walking/throwing/jumping
routine, replacing generic flying pursuit. Its profile supplies 16 HP, 30-point defeat, 45-cycle
lifetime, spawn positions, source animations, aim-gated firing and all 32 projectile direction
indices. The common projectile pool now stores health, so this actor's projectile survives one
weak hit and breaks on the next; POW bypasses that durability. Source comparisons cover
10,920 body/projectile ticks and 1,920 constructor attempts. A real round-six row verifies
emergence, nonfatal/fatal body hits, firing, two-hit projectile destruction and independence
from parent death. Shared pool contention, source spawn scanning cadence and full routes remain
unverified.

Small projectiles now retire at the source's screen-relative boundaries, releasing their slots
before their animation would otherwise end. Paired flyers reuse the same axis check. The
horizontal/vertical one-pixel difference and x-before-y retirement order match 279 source
loader cases and 837 translated world-coordinate checks. Eight cartridge cases verify removal
outside all four sides and retention inside them; existing thrower/spitter/pair traces still pass.
