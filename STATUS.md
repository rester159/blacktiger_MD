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

The 59 placements using bank 1 ACBE/ACD3 are locked containers, not falling rocks. Closed
containers are now stationary and weapon-immune, and the fake break-for-200-points/50-coins
path is removed. Native content selection uses the eight source round tables, eight swaps and
two RNG updates per source task yield; 128 controlled source-shuffle comparisons cover it.
The contents remain stable on a same-round restart. Cartridge checks cover both actual closed
container variants and selection by persistence ID. The three constructor phases and six content
types are extracted for the next implementation work. **Key inventory, opening, trap spawning,
reward collection and opened/collected persistence are still missing**, so containers are not yet
fully ported. Exact source global startup/RNG scheduling also remains unverified.

The six container contact handlers now also have a shared native effect kernel, checked against
144 original-ROM calls covering zero/nonzero keys, both opening states, all four coin values,
16-bit money wrap and health restoration. Coin pickups award 50/100/500/1000 money and no
score; the source's second update changes the decimal money display. This kernel is deliberately
not yet called by gameplay: opening animation ownership, inventory acquisition, six-part traps
and persistent reconstruction must be connected before the closed-container behavior changes.

Container gameplay now uses native closed/opening/reward/empty animation states. Contact consumes
one key, waits for the source opening callback, then permits a separate coin/heal pickup. Camera
retirement reconstructs opened and collected states by the original eight persistence IDs. Trap
contents create six independently animated small parts; movement, delayed contact enable and
retirement match 2,880 original loader ticks in both directions. Twelve cartridge cases cover
both constructor variants and all contents, including zero-key refusal and empty reconstruction.
Keys currently have a separate zero-initialized inventory; source starting keys, pickups, shop
acquisition and HUD are still unported. Healing uses the provisional native maximum of four HP.
Trap ground placement follows the source six-height search but is not yet oracle-checked; the
native trap pool is separate from other small actors, and death/restart persistence needs an
original lifecycle comparison. These tests do not establish natural chest progression or a full port.

The placeholder four-item shop is replaced with the source ten-item catalog: four weapon
upgrades, four armor grades, keys and antidotes, plus exit. All eight difficulty price tables
are extracted; the cartridge uses the observed default DIP setting (index four). Purchases
refuse insufficient funds, already-owned equipment and quantities at 99 without charging.
Native controls buy keys for 30 and show their count on the HUD; a purchased key opens an
actual source container row. The 322 original-handler comparisons and cartridge checks for
all ten goods pass. Antidotes cost 150 and support stored inventory or clearing the native
poison state, but enemy poison onset/countdown and consumption are not yet ported. Initial
inventory, loose key pickups, complete equipment stat mapping and original shop presentation
remain unfinished. The new two-column menu adapts the catalog to the Genesis screen. A GCC
16 LTO unaligned widened byte read was eliminated with a volatile difficulty byte. Renderer
regressions now compare the playfield below the 16-pixel HUD, retaining the pinned old ROM
reference for sprites; the new HUD/shop have linked cartridge captures and behavior tests.

Starting resources now follow the source initialization slices: three default-DIP lives, one
current/maximum HP, two armor points, 200 coins and zero keys. All native score awards use a
shared progression routine. Maximum health increases at 2,000/12,000/22,000/32,000 points,
one threshold per award, without healing damage; the HUD shows current/maximum HP. NPC,
chest and hidden-item healing and round-entry restoration use the earned maximum, up to five.
Twenty original score-task comparisons cover exact thresholds and neighboring values; linked
boulder awards cross all four thresholds and verify no immediate healing and correct respawn
restoration. Five-HP fixtures check each healing family. Full original death/continue inventory
reset semantics, maximum-score saturation, loose keys and provisional magic remain unported.

Life loss now restores two armor points, clears poison and consumes the final life before
game over. Weapon tier, coins, keys, antidotes, score and earned maximum health survive a
restart. Consumed placement rows remain consumed while active rows become eligible again;
opened/collected chest flags and broken/collected wall state survive the same-round restart.
Fresh rounds and new games clear those world flags. Source witnesses cover the death writes
and four-byte persistence-copy loop (clear bit zero only); linked tests use actual chest and
hidden-wall collection, life loss and a fresh game. Original checkpoint camera/position,
continue behavior and death presentation timing remain unfinished. New-game input preserves
the held Start latch so the same press cannot immediately pause gameplay.

Same-round life loss now selects the original checkpoint through a shared 256-pixel region
lookup: 32 entries per round, with 8x4 or 4x8 indexing according to the map orientation.
All eight grids and the player spawn offset (112,144) are extracted; fresh round entry also
uses that offset instead of the provisional (128,144). The lookup matches 768 original
calls spanning every cell, boundary offsets, 16-bit wrapping and both source save slots.
Thirty-two linked DEAD-to-PLAY cases verify camera/hero placement and life debit. Some table
entries address unused regions, so injected lookup coverage is not proof of natural route
reachability. Continuous source camera limits, scrolling and continue behavior remain unported.

Continue now restores the configured starting life count and clears score while retaining the
round, checkpoint selection, equipment, coins, keys, antidotes, earned maximum health and world
persistence. Ending/title Start remains a separate new-game reset. Source witnesses cover the
life restore and eight-digit score clear; cartridge life-loss tests check retained chest/wall
state and inventory through Continue, then verify a separate fresh-game reset. Holding Start
through either transition does not pause. The native port currently offers free Continue; the
original credit handling, countdown presentation and continue DIP option remain unimplemented.

Bank 0 B84F (32 placements) now uses a shared native stationary caster routine.
Its body matches 18,000 original-loader ticks across facing/random choices and repeated
weak/strong hits: six initial HP, four damage layers, four HP on subsequent layers, recoil
immunity and a 100-point final reward with source loot/persistence. The 16-direction shell
and independent medium explosion match another 8,640 source ticks, including cycle expiry,
weapon hits and contact-triggered placement. Linked cartridge checks exercise a real source
row, natural firing, all four layers, independent shell lifetime and one-point blast damage.
Source shared small/medium pool contention is not reproduced: native effects use dedicated
bounded pools. Chain geometry, exact scheduling and complete natural routes remain gaps.

Bank 3 AAB3 (19 seed placements) now uses a shared native falling/splitting crawler family.
The seed waits for the original byte-wrapped proximity interval, falls under quarter-pixel
acceleration, opens, and spawns two independent bodies. All three use the source terrain,
facing, walking and damage transitions, including the source's unusual weak-hit retirement
without score and ten-point strong-hit reward. Ninety-three controlled cases compare 21,840 source
loader ticks; 18 split observations check child positions. The linked cartridge verifies a
real placement, dormant immunity, the three-body split and both damage paths. Screen-attack
pickups bypass weapon immunity for seeds and casters, matching source forced-death handling. Shared source
small-pool contention, exact scheduling and full natural routes remain unverified.

The bank 1 flying hunter (9F83) and boss variant (9FC4) now have a native shared body
kernel. It matches 57,600 original-loader ticks across 192 cases: all weighted steering
choices, 16-direction aiming, screen-edge recovery, attack/immunity phases, three damage
layers (20 HP normal, 46 HP boss), recoil and the 500-point final award. Eighty-one compiled
animation segments now drive both gameplay variants and their projectiles. The shared native
shell/explosion engine matches another 8,000 source ticks across all directions, terrain
impacts, expiry, normal weapon hits, boss-shell immunity and contact bursts. Cartridge checks
cover real normal/boss spawns, natural firing, all three layers, the 500-point reward and
death-animation completion before clearing actors/effects and entering round clear. Original
boss health display, exact global pool contention and full round-clear presentation remain.
The source screen-attack filter also establishes that special-contact caster shells (36)
and hunter shells (40) are excluded; caster shells now survive POW, with a linked-cartridge regression check. These body checks do not establish full-family fidelity.

Bank 1 92E6 and 8D33 now share the native teleporter family: 60,000 source body ticks and
1,456 constructor attempts verify relocation, first-spawn/45-attempt recurrence, five attack cycles,
18/8 internal durability, phase-dependent damage halving and a 100-point final reward. Its
six-part attack shares the container-trap engine with separate source animation roots,
origins, and contact dispatch. Another 2,880 source ticks check all parts in both directions.
Linked cartridge checks cover actual round-six and round-four rows, both six-part attacks,
ordinary armor damage, status contact,
antidote consumption, shop cure, recurring construction and POW defeat.

The attack's special contact 43 reverses horizontal controls; it is separate from poison.
E919 provides a shared 60-tick contact gate, or 30 ticks after consuming a stored antidote.
The native status routine matches 349 source contact/timer cases and 128 control masks;
health and armor are unchanged. Shop cures clear both statuses, while unrelated purchases
preserve the distinction. The source diagonal posture dispatch for input 5, status palette
flashing, full poison lifecycle and exact constructor scan scheduling remain unverified. Shared source
small-pool contention and natural full-game routes also remain unverified.

Bank 1 8A5D, 8A03, 8B9B and 8BF5 now share a native recurring ground-flame routine.
Source comparisons cover 1,024 body ticks and 41,328 constructor attempts, including screen bounds and byte-wrapped
proximity boundaries. The flame starts harmless for six ticks, damages for 36 ticks, then
recovers for six ticks before retirement. Every twentieth eligible constructor call can
spawn another flame; the primary row flag does not suppress recurrence. POW retires it
without awarding points or a kill. Linked cartridge fixtures cover actual rows in rounds one, two, four and five, natural
retirement/respawn, both contact phases, armor damage and POW removal.
Exact global constructor scheduling, source pool contention and audio remain provisional.

The two special ground flames apply poison (contact 38) and ordinary contact damage.
They share the status gate with reversed controls. An antidote prevents poison for that
contact and starts a 30-tick gate; without one, poison is set and the gate becomes 60 ticks.
The status oracle stops at the ordinary damage dispatch, while cartridge tests confirm
armor damage with and without an antidote. The medium contact dispatcher applies poison
even during ordinary hurt invulnerability; a cartridge case verifies poison without armor loss. Poison suppresses native dagger creation but
leaves the primary weapon available, matching the source dagger-entry guard. Round entry
clears poison, and the existing shop cure removes it. Source poison lifecycle outside these
paths and palette presentation remain unverified; no damage-over-time behavior is assumed.

Bank 1 98A3/98E8 now use a shared native large wave-boss engine, replacing provisional
walker behavior in rounds five and seven. Thirty-one compiled segments drive both 64x64
bodies and their wave-seeding projectiles. The 192-case body oracle compares 230,400 ticks:
engagement, all weighted movement choices, screen-edge return, facing, initial and later
hit callbacks, five/six damage layers, 5,000/15,000-point rewards and the clear callback.
Small projectile allocation is kept available in the body oracle to isolate controller
behavior; 3,840 additional source ticks cover both projectile directions, variants, heights,
terrain branches and retirement. Native seeds dispatch the existing ordinary/special
six-part wave engine. Cartridge tests verify actual boss rows, natural seed/wave attacks,
all health layers through head hits, rewards, persistence and cleanup before round clear.
The renderer draws all sixteen original sprite pieces with the native palette conversion.
Boss health display, the separate death-flash task, full player/chain animation integration, exact shared-pool contention and the complete clear presentation remain gaps.

Large-actor collision now has a reusable native geometry routine sourced from the original
chain, dagger and player-contact handlers. Source probes cover 2,340 main-weapon cases,
2,340 dagger cases and 4,680 normal/alternate player-posture cases for both wave-boss
profiles, including offscreen/wrapped coordinates and asymmetric bounds. The dagger's
weak-point calculation preserves its distinct one-pixel boundary. The boss adapter now
uses screen coordinates and extracted template dimensions. Cartridge tests confirm head
damage and non-damaging body blocks for both weapon kinds and both bosses. The native
player still uses normal posture and provisional main-weapon animation/extents; this check
does not establish full player attack fidelity or the entire original collision schedule.

Bank-zero AB33/AB4A/B1C1/B1D8 now share a native flail-wielder controller and independent
weapon pool. The source graph contains 108 compiled segments across the two health/speed
profiles and both starting directions. A 144-case oracle compares 57,600 body ticks covering
proximity activation, facing, walking, obstacles, jumps, falling, fractional gravity, attack
linkage, 24/56 internal health, recoil, defeat and 20/50-point rewards. Another 3,600 source
ticks cover the weapon profiles/directions, trajectories, destruction and parent cancellation.
Cartridge checks cover actual rows in rounds one, three and seven, natural attacks, recoil
cancelling a linked weapon, defeat rewards and retirement. B1D8's only extracted row is at
X=16352 in a 2048-pixel-wide round; its mirrored profile is exercised in a controlled slot,
not reported as a naturally reached placement. Original scan behavior for that row remains
unverified. Native flail allocation has its own pool rather than original global contention.

Flail contact 42 differs from ground-flame contact 38: its antidote/gate paths return without
ordinary damage, while an unprotected contact applies poison and two damage. The second
flail profile deals one ordinary damage. The expanded status oracle checks those dispatch
branches; cartridge fixtures confirm both damage values and the zero-damage protected paths.
Native chain geometry and global contact scheduling remain separately scoped limitations.

Shared offscreen actor cleanup now clears only the active bit, preserving the consumed bit
when a defeated actor leaves the view before its death animation finishes. A cartridge
regression moves a dying flail-wielder offscreen and verifies that it stays consumed.

Bank-three B153 and bank-seven A3B6 now reuse the AAB3 crawler controller. The three
falling-seed families share proximity activation, quarter-pixel gravity, three-body splitting,
terrain walking, facing, weak-hit retirement and fatal-hit animation. Their extracted profiles
retain durability 2/8/16 and rewards 10/15/15. The expanded oracle compares 65,520 ticks in
279 cases and 54 split events against the arcade. Cartridge tests exercise actual placements
in rounds one, two and six, including initial immunity, splitting and weak/fatal damage.
A3B6 uses the shared poison-contact-42 handler. Global small-actor pool contention and full
natural routes remain unverified.

The shared pre-allocation schedule for bank-two 8344/9AF6 is now native: screen bounds,
byte-wrapped ±48/±32 player proximity, an initial attempt, forty eligible calls of waiting,
and consumption on the second allocation attempt even if the actor pool is full. Secondary
row counters survive checkpoint restarts and reset with a new round. A 568-case oracle checks
24,424 calls including boundaries, nonzero row bytes, full pools and byte overflow. Cartridge
checks cover actual round-two and round-seven placements, first defeat preserving the second
attempt, delay pausing out of proximity, and no third appearance. This is constructor coverage
only: both actors still require their shared movement/attack graphs, layered damage and rewards.
Their source body callbacks are 83BC/9B6E; initial templates are 8899/A07D, and their six-part
projectile templates are 88C9/8989 and A0AD/A16D respectively.

Both reinforcement fighters (bank-two 8344/9AF6) now use one native body controller and
six-part projectile pool. The 90 compiled body segments preserve distance-weighted choices,
walking/obstacle responses, both jump patterns, quarter-pixel gravity, two/four health layers,
recoil, defeat and 20/80-point rewards. Both source routines unconditionally choose the
right-facing jump windup; the native graph preserves that behavior. Projectile graphics and
motion are identical between the profiles and share twelve clips for six parts in two directions.
Only the third part carries the source 40×4 contact extent and one damage; the other parts
are visual. Independent projectile tests compare 4,608 source ticks, including offscreen
retirement. Cartridge tests cover actual placements, natural attacks, weak and fatal hits,
every health layer, rewards, retirement and projectile contacts. Normal player posture is
used in the cartridge: the second profile's low-target variant is source-verified in host tests,
but connecting it requires the remaining native player-posture work. Separate projectile pools
still do not reproduce global source allocation contention.

The reinforcement body oracle compares 199,680 ticks in 416 cases, including full projectile
pools, and 1,362 six-part launch snapshots. Reward-table extraction corrected the stronger
fighter to 80 points. The two templates supply initial health 4/18 and layer counts 2/4.
