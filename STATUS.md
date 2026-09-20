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
source constructor, nonfatal/fatal projectiles, shields, score, and retirement. Body/weapon/player hitboxes still use provisional native geometry.

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
