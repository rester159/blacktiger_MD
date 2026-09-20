# Status

Deliverable: an SGDK development cartridge and a reproducible new repository.
User's requested complete native Black Tiger port: **not achieved**.

The main remaining shared systems are compound-boss contact
geometry and screen-edge behavior, global camera/scanner
cadence, presentation and audio. All eight maps use one renderer and game loop;
normal locomotion and the known major enemy/boss families now have native routines.
Injected actor/ending tests do not establish natural full-game completion.

Known native issues: frame overruns on denser routes; unverified PAL timing;
placeholder sound effects and incomplete music selection; incomplete combat integration and parts of presentation. Exact
cadence, cartridge hash, and test counts live in JSON reports and `dist/build.json`.

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
post-death interactions and single-life respawn. Shared crouch/jump contact rules and source death animations are now integrated; see the latest status entry.

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

Bank-four A4D0 now uses its source trigger/entry constructor: player proximity within the
byte-wrapped ±16 rectangle, no allocation when the pool is full, entry at screen X=224/0
according to normal player facing, and six ground probes from screen Y=96 through 176.
Failure to find ground preserves the original active row bit despite creating no actor.
A 616-case source oracle covers boundaries, persistent flags, pool failure and floor-search
limits. Cartridge fixtures exercise both directions at the actual round-seven row 29.
This is constructor coverage only; its body, aimed projectiles and death behavior remain
provisional. The source uses player direction/posture byte E901; native facing covers the
normal 0/4 directions, with the wider player-posture port still outstanding. Body template
AA0C and callbacks A564 onward are the next actor work; projectile templates AA3C/AA5C
use direction tables AEEE/B0DA.

The bank-four A4D0 caster now has a native body and two aimed projectile profiles. Its 107
body segments cover five weighted jump patterns, dash/contact-triggered strike, fractional
gravity, single/double shots, two 64-health layers, recoil, screen-relative relocation,
100-point defeat and persistent retirement. The original medium-actor collision loop gates
hits by mode, not the actor's 80/40 state byte: this enemy remains hittable after first-layer
recovery without restoring that byte. The native implementation and body oracle preserve
that distinction. The source's unconditional relocation animation branch is also retained.
A 768-case oracle compares 368,640 body ticks, including available/full projectile pools.
Both projectile types use the shared aim routine and 17 source direction clips each;
9,792 source ticks check motion, terrain impact, weak/fatal hits, animation and retirement.
Cartridge fixtures exercise the actual round-seven placement, a natural aimed attack,
first-layer recovery, final reward/consumption, and projectile damage 1/3 and destruction.
Original global actor-pool contention, alternate player postures, and full routes remain gaps.

Bank-three B7F3 was incorrectly classified as a boss. It is a fourth small falling-seed
family, now handled by the shared crawler code with its source health 3 and reward 15.
The profile adds five weighted walking/hopping choices, forward/reverse/vertical jumps,
ceiling checks, center-foot wall probing and gravity until landing. The expanded crawler
oracle checks 411,360 ticks in 1,722 cases and 342 three-body splits, including all sixteen
random-table inputs. Cartridge tests cover the actual round-five row 51, initial immunity,
splitting, weak/fatal hits, rewards and no round clear. The earlier bank-zero B1C1 flail
fighter's stale boss classification was removed as well; its ordinary-enemy behavior was
already independently verified. The remaining bank-two definition was subsequently identified and ported below.

Bank-two 8EF4 is the third reinforcement fighter, sharing the same native constructor,
body controller and six-part projectile routines. Its extracted graph adds 47 segments,
12 HP per layer, two layers and a 30-point reward. Its stale boss classification is removed.
All three profiles now compare against 299,520 original body ticks in 624 cases, including
1,999 six-part launches, 6,912 projectile ticks and 36,636 constructor attempts. The actual
round-four row 51 cartridge fixture verifies attacks, damage, both health layers, reward,
retirement, two appearances and persistence. All projectile frame data are asserted equal
across the three source profiles, so the cartridge retains one shared set of shot clips.
Three unported definitions remain: bank-three 8000, 991D and 9B24, all large dragon bosses.
Their 128-by-64 sprite loader and shared decision family have been identified, but their
native behavior, weak-point collision, attacks and presentation are still outstanding.

The three dragon body profiles now have one native C controller and 139 extracted
animation segments. The body oracle matches 427,140 ticks in 384 cases, all three
completed death sequences, weak/fatal hits, recovery decisions and 2,625 projectile
launch snapshots, including available/full projectile pools. One shared attack returns
through the middle dragon's decision table even on the final dragon; this source behavior
is preserved explicitly. Both six-part ground-flame profiles reuse the container trap
controller with 5,760 source ticks covering animation, displacement, contact enable timing
and retirement, plus ordinary/reversed-control contact dispatch. The body and wave-spawn
entry points are not yet called by the cartridge game loop: projectile owners, 128x64
rendering, collision and integration remain outstanding. Source details and next steps
are recorded in reference/dragon_audit.md. These subsystem tests do not prove boss or
round completion in the cartridge.

Dragon integration is now active in the cartridge: all three source placements use
the native shared body controller, 128x64 sprite renderer, targeted weak points, aimed
orbs, medium explosions, ground-flame seeds and the shared six-part flame controller.
Projectile comparisons cover 33,120 ticks in 207 cases, including terrain, fatal hits,
edge retirement, seed-to-wave positions and full explosion pools. The source full-pool
failure reads a zero-duration frame; the native counter matches its 256-tick meaning,
and every possible 16-bit Y retires before any later misaligned record could execute.
Wide collision matches 31,200 source cases, including the final dragon's signed head
offsets and the source dagger-Y carry. Actual round 3/row 79, round 6/row 103 and round 8/row 96
fixtures verify natural attacks, ordinary/dagger damage, all 3/6/8 health layers,
1,000-point rewards and round-clear callbacks. Cartridge checks also verify orb and
explosion contact damage and seed/death-phase immunity. Screenshots confirm all 32
sprite pieces render. Dynamic boss palettes, health bars, full death presentation,
source global pool contention and natural complete routes remain unverified/incomplete.
The next major shared system is the exact native player controller and chain weapon.

Orb contact conversion was also corrected: source contact41 creates an explosion at
the player's origin and retires the orb next tick; the explosion applies damage.
The native full-contact-pool path discards the orb without damage instead of following
the source's misaligned animation pointer. Cartridge tests cover both outcomes.
For the upcoming player work, the prior repository has partial native walk/fall code
in game/src/player.c and source ownership evidence under reference/arcade/oracles/
BT-RE-006: fixed1E17 selects bank7 and enters8000. Those older routines are source leads,
not evidence of a completed player port.

Shared native player locomotion now replaces the provisional Q8 movement in the
cartridge across all eight rounds. It implements source input history and reversed
controls, walk/crouch selectors, ladder attachment/detachment, seven jump directions,
one-time air steering, pre-movement collision probes, quarter-pixel velocity gravity,
integer position integration, landing and logical camera-return state. Comparisons
match 24,620 source updates across 309 cases. All 960 armored/unarmored gameplay
frame records are compiled, including crouched selectors; 48 hardware-sprite checks
and real input checks verify the cartridge path. Reinforcement aiming now sees the
player's low-posture state. Global camera clamps, attack/jump-attack timing and chain,
other alternate collision postures, movement sounds, hurt/death and presentation
remain unfinished. `reference/player_audit.md` records the implemented scope and
already-audited attack/chain source to avoid repeating that work.


Source-derived chain attacks and three-dagger volleys now replace the provisional
player shots in production. The common controller includes all five reaches,
six-update windup, per-update chain extension, hold/release, collision shortening,
button-history retriggering and distinct jump-attack branches. Motion/attack checks
match 56,720 original updates in 719 cases. The dedicated nine-dagger pool matches
28,800 slot updates, including terrain/hit explosions and full-volley allocation.
Source chain geometry matches 1,306 small/medium boundary cases. Real Genesis input
matches 300 attack updates, renders five weapon tiers and verifies crouched-chain
hits, hit shortening and suppression of subsequent targets. Existing family tests
pass with body-damage fixtures isolated from independently hittable projectiles.
Player death, alternate contact postures, some compound-boss geometry, global scan
ordering, impact presentation and audio remain unfinished; these checks do not
prove a natural full-game route. See `reference/player_audit.md` for exact scope.


Crouching now changes live collision as well as graphics. Small/medium actor
contacts, ordinary projectiles, skeleton weapons and statue/hunter explosions use
the source low-posture origin and fixed actor extents; an active jump overrides
that posture. Wave bosses and dragons now use their alternate contact branches.
Checks match 2,352 source boundary cases across twelve shapes and include eighteen
real-input cartridge collision cases. Screen-edge wrapping and remaining compound
boss geometry are not established by those interior-boundary checks.

## Native player death sequences

Four shared source-derived clips now handle ordinary and hazard deaths in both
facings. Each contains 33 two-body frames spanning 328 updates, followed by the
restart callback on update 329. Native C performs signed sprite movement, palette
and flip selection; no original instructions run in the cartridge. Damage callers
pass attacker position for ordinary fall direction. Hazards use player facing.
Twenty arcade oracle fixtures compare 6,580 updates, including coordinate wrapping.
Cartridge fixtures verify both ordinary directions, every frame, hazard selection,
and exactly one life deducted after the animation finishes. Armor-break fragments,
source hardware edge hiding and full continue presentation remain unfinished.

## Shared armor-break fragments

The four armor fragments now use the common native animation loader, with source
frames compiled offline. Exact armor depletion, damage overflow, hazard death and
timeout all create the effect; remaining armor is cleared on hazard/time death.
Twenty original-ROM fixtures compare 3,600 updates including offscreen retirement.
Six cartridge fixtures cover triggering/non-triggering hits, invulnerability and
timeout; rendered capture confirms four separated fragments. Source small-pool
allocation competition remains separate from this dedicated four-slot effect pool.
The hazard oracle previously addressed F3B0/E919 for armor/invulnerability; it now
uses the audited F3AD/F424 and its 126 observations were regenerated and passed.
Audio remains placeholder; this implements sprite behavior, not original sound.

## Shared game-loop performance

Game-loop profiling identified repeated empty-pool collision scans and repeated
boss-family scans. Projectile collision passes now determine populated families
once, retain the original family/contact order, and skip empty families. Calls
for inactive projectiles are avoided; a single actor scan handles ordinary-scene
boss checks. With no chain or flying dagger, the weapon collision pass returns
immediately. No animation, movement, damage, or spawn cadence was reduced.

The same round-entry benchmark improved from 90–157 to 107–172 logic updates per
180 video frames. Sampled median game cost fell 22–38%; the exact per-round results
and both cartridge hashes are in reports/performance-comparison.json. Faster
simulation changes distance traveled during this video-frame window, so this is
an approximate route sample, not a matched-state microbenchmark. Full-rate play,
worst-case loads, PAL and hardware performance remain unfinished.

## Contact/render overhead and bounded VBlank scheduling

Native actor families no longer compute an unused pre-movement contact box before
their own post-movement contact check. Rendering skips inactive projectile slots
before calling frame getters. Existing pre-movement contact semantics for sentries,
skeletons and pickups are retained.

On NTSC, a transfer queue of at most 1,024 bytes may use the current VBlank only
when it is still within raw scanlines 224–230 and has not already been presented.
Other cases retain SGDK's strict next-VBlank-start path; PAL is unchanged. Counters
record opportunistic flushes and any finish outside blanking. Eight 600-frame route
samples verify no such overruns and no double-step on any sampled video frame;
600 paused frames produce exactly 600 updates. The 180-frame profile now reaches
116–174 updates across the sampled entries. Full-rate routes and real-hardware
validation remain incomplete. Detailed evidence is in frame-scheduler-tests.json
and performance-profile.json; this is not a full-game timing guarantee.

## Native round music

All eight round FM tracks now play on the Genesis YM2612 through music.c. Offline
MAME observations run the supplied sound driver only during extraction; the ROM
contains typed timed register data and a native C player, with no sound CPU code
or emulation. A full channel-state/register repeat identifies each intro and loop.
The original round-start routine at fixed233B selects commands 21–28.

Redundant register writes are removed, frequency numbers are corrected for the
Genesis FM clock, and six FM voices map to the two YM2612 register banks. Data
uses 261,390 bytes, including carrier-only attenuation to prevent mix clipping. Timing follows elapsed video frames, including missed gameplay
frames, using the source timer ratio rather than one update per game tick. PAL
has a separate clock accumulator and pitch adjustment; PAL hardware remains untested.

Host checks cover 103,666 sequencing/clock batches through intros and two loop
wraps for every track. Cartridge checks verify eight selections, rendered audio,
continued tempo while paused, and stopping on game over. Music continues through death and restarts on respawn, while clear/ending
currently stop it; proper boss themes, jingles, source priority/resume behavior,
original SSG effects, mix/timbre comparison and hardware listening remain unfinished.
The existing PSG effects remain provisional. reports/music-preview.wav is a short
rendered first-round sample, not an original arcade recording.

## Boss themes and finite FM cues

The shared player now supports the complete 25-track FM data catalog at commands
20–39 (38 is a control command). Three boss themes are selected at real boss spawn
using the fixed5A30 per-round table: 29,29,2A,29,29,2A,29,2B. Shop entry selects2C;
shop exit restarts the round music. CLEAR selects32, or33 for the final round;
33 continues across the transition into ENDING. GAMEOVER selects31 once and lets
it finish, without restarting it. One-shot tracks stop at their observed source
terminal event; loop tracks preserve their intro/loop boundaries.

Native data occupies 429,789 bytes and the cartridge remains below4 MiB. Host
checks cover all25 programs with both regional clock accumulators. Cartridge
checks exercise all8 actual boss placements and production mode changes; short
audio samples from all25 tracks are non-silent and unclipped. Additional catalog
cues remain unwired pending their source event/presentation ports. The prototype
CLEAR duration can still interrupt its full jingle; full cutscene timing, continue
flow, source priority/resume rules and original PSG effects remain unfinished.

## Alternate-area source audit

Located the 12 omitted invisible transition triggers in rounds 1–6 and extracted
all destination cameras, return offsets, and normal/alternate background update
lists (`reference/bonus.json`). These are gameplay transitions, not optional
hidden-item decorations. Native integration remains required. The has-entered
latch persists after exit; return X adjustment wraps within its low byte. See
`reference/bonus_audit.md` for the source contracts and remaining integration.

The isolated original-ROM oracle passed 225 contact-gate and camera-policy cases.
The cartridge is unchanged in this audit; these results do not prove native
alternate-area gameplay.

## Native alternate-area integration

Implemented the shared alternate-area contacts and camera transition for all 12
source triggers across rounds 1–6. Rewards and consumed objects survive the
transient-pool reset. Doorway tile/collision changes use the existing Genesis
palette mapping, with music and life-restart latch handling. Native camera/gate
logic passes 225 source cases; cartridge fixtures cover all 12 contacts and VRAM.
Background changes currently hold the first source animation phase. Animated
phase timing, transition presentation and natural room routes remain unfinished.

Validation completed for the current ROM, including normal grounded round-one
entry and destination hidden-wall spawning. Existing injected-state tests now
wait for mode/VDP completion where fixed short delays raced the running cartridge.
Audio mode tracking uses the mode captured at the start of its update.

## Native animated backgrounds

Compiled both source background phases and their collision codes for every
round/alternate-area state. A shared native 26-tick clock preserves staggered
four-bank updates. Source capture checks 384 yields and 2,376 byte writes; native
clock comparisons and 12 fixed-camera cartridge rendering cases pass. The tile
cache updates changed visible cells and preserves hidden-wall overrides. Exact
whole-board task timing/lifecycle behavior and transition fades remain unverified.

Animation updates now reject unchanged banks and offscreen patches before tile
lookups. The current 180-frame entry profile spans 99–168 logic updates across
rounds; sustained 60 Hz remains unfinished. Paused rendering fixtures drain the
active gameplay frame before replacing actors and private animation state.

## Shared actor dispatch

Replaced repeated render-family scans with a generated native function/layout
table for all 66 actor definitions. Common actor updates use the same table's
behavior selector, preserving movement/contact ordering and early boss paths.
The 180-frame entry benchmark improves in all eight rounds (119–173 updates),
with the existing pixel fixtures unchanged. See `reference/dispatch_audit.md`.
Sustained 60 Hz and full natural routes remain unverified.

## Native round completion

The shared clear routine now waits for landing or ladder descent, plays the
source victory sequence for all five weapons, restores missing armor to level 2
without healing, and awards 300/500/800/1200/1600/2400/4800 Zenny across rounds
1–7. Round 8 branches to the ending after its shorter common animation and
skips the bonus. Ordinary bonus holds last 240 updates.

The source capture covers 20 complete animation profiles and 32 payout cases;
the native host comparison checks 3,080 animation updates, sprite bytes, timing,
resource changes and integer overflow. Cartridge fixtures exercise all 20
profiles, their hardware victory sprites, the airborne landing wait, and both
round-transition branches. Boss families share one clear
entry point. Source bonus-screen backgrounds, fades, final cutscene, and a
natural complete playthrough remain unfinished. See `reference/clear_audit.md`.

## Collision dispatch performance

Vulnerability checks now use native callbacks compiled per actor definition,
preserving the previous family precedence and special cases. Skeleton weapon
contact processing reuses an active-slot mask from its update pass. The same
180-display-frame entry test improves all eight rounds to 131–176 logic
updates, compared with 118–175 before these changes. Full-route 60 Hz remains
unachieved; exact measurements and limits are in `reference/dispatch_audit.md`.

## Timed game-over and console continues

Last-life exhaustion now shows the seven-second game-over notice followed by
a 9-to-0 continue offer (75 updates per digit). The original continue FM cue
34 plays during the offer. Start accepts a free console continue, retaining
world/inventory progress and resetting score/lives; holding Start does not
pause the resumed game. Expiry returns to the title, where starting a new game
clears progression. Source waits and polling instructions are hash-witnessed;
host tests cover exact durations and the last poll, and cartridge tests cover
real last-life entry, both outcomes, music and inventory. Arcade coin handling
is replaced by free continues. Original artwork, fades, and high-score initials
are still unfinished.

## Route validation and original controls

Added a bounded route search that compiles the production movement, contact and
alternate-area routines for host execution. Found paths are replayed through
those routines from their initial states. Current terrain plans reach boss areas
in rounds 1, 6, 7 and 8; searches for rounds 2–5 remain inconclusive. Combat,
breakable walls and other gameplay interactions are outside this model.

A new cartridge replay tool starts from the title, uses only controller inputs,
and saves a run-length-encoded video-frame input tape. A second fresh boot
reproduces the final state from the tape. The current round-one attempt dies
before the boss; it is evidence of a reproducible gameplay prefix, not completion.
See `reference/routes_audit.md` and the route reports.

Removed the prototype's C-button magic charges. The original player interface
has two action buttons (attack and jump); source POW pickups retain their
separate screen effect. An actual-cartridge comparison checks that repeated C
presses leave movement, attacks, daggers and game state unchanged.

## Route diagnostics follow-through

Pre-opening the known hidden walls in the host route model did not resolve its
round 2–5 searches; production collision remains unchanged. Added bounded
controller exploration in isolated emulator-process copies, followed by a
fresh-title input-only replay comparing persistent RAM and CPU PC/SR/SP. Standard savestate
exploration failed replay verification and was rejected. The verified controller
currently stalls mid-round one; this is a controller limitation, not a completed
playthrough or evidence justifying a terrain change. See `reports/route-play.json`.

## Original round-bonus artwork

Replaced the placeholder clear panel and scrolling terrain with the source bonus
artwork and lettering for all seven ordinary rounds. Shared Genesis patterns use
two exact RGB333 background palettes and one character palette; no additional
color quantization is needed. Original digit glyphs display the native current
Zenny balance. Gameplay sprites are hidden and the next round rebuilds its
terrain cache and palettes. Original-ROM setup captures and cartridge VRAM,
pattern, palette, balance and transition checks cover all seven screens.
Fades, original HUD, final cutscene and natural full-game completion remain open.

## Native final story and credits

Replaced the static prototype ending with the original timed story, credits and
final backdrop. A native sequencer handles 560 character writes, page holds,
clears, palette steps and scene changes across 4,515 source-observed updates.
The opening terrain colors are adapted through the existing Genesis palette
mapping; credits artwork and lettering retain their RGB333 colors. Shared glyphs
occupy previously unused VRAM, preserving the preceding victory picture during
the story. Only dirty text rows are uploaded.

After the ending, game over runs without a continue offer, matching the source's
completed-round branch. Host checks compare every observed update; cartridge
checks cover all pages, actual VRAM/palettes, music, repeated Start, terminal flow
and starting a new game. Original HUD, high-score entry, whole-board sprite and
scheduler comparison, natural full-game completion and hardware timing remain
unfinished. See `reference/ending_audit.md`.

## Shared native sound-effects player

Added source-derived finite SSG effects with two priority-controlled native slots,
four timer-phase variants, regional timing and a Genesis PSG mixer. All 34 finite
programs are available; player attack, jump and death now use their witnessed
source commands. The extra prototype clear chirp is removed. Native tests compare
all finite streams with the original driver, and cartridge checks render every
supported effect, verify finite stopping and unclipped isolated/music-mixed audio,
and exercise actual player bindings.

Two sustained commands (14/3C) remain unsupported rather than receiving fabricated
endings. Other gameplay-event bindings still use provisional cues. PSG voice count,
noise gating/timbre and frequency range require documented adaptations; source
command-queue contention, detailed listening and hardware/PAL validation remain
unfinished. See `reference/audio_audit.md`.
