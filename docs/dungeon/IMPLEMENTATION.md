# THE DUNGEON implementation

User-facing entry: HOME > THE DUNGEON. The supplied document calls the mode THE LAST HOUR; retain that name as the run's subtitle. Arcade, normal Home, and Boss Rush remain separate.

## Milestone gates

- M0: freeze palette allocations and enforce contrast/reserved-entry checks at build time.
- M1: playable persistent clock, 16 fallback stages, setup/intro/play/death/gate/results lifecycle.
- M2: affixes, bounded spawn manager, verified hardware shadow/highlight behavior.
- M3–M10: proceed in the supplied order. Do not label the full mode complete until its acceptance tests pass.

## Hardware corrections to the supplied spec

- The existing port uses H32 (256 px): the stricter actual limits are 64 sprites, 16 per line, 256 sprite pixels per line. Retain arcade framing; Dungeon must satisfy these stricter bounds.
- Palette 1 has 15 opaque entries: use 7 accent entries, 6 HUD/font entries, and 2 immutable clock entries. Entry 0 stays transparent.
- Shadow/highlight reserves palette 3 entries 14 and 15 as operators. Use 7 base-enemy entries, two three-color affix ramps at 8–10 and 11–13, and the two operators. Ordinary enemy patterns must never use pens 14/15.
- Two heroes using different armor ramps within palette 2 require tile copies with remapped indices. This is a VRAM cost, although it reuses the same original artwork. User approved reserving the tile copies.
- User requested a fresh random seed each run instead of Daily dates. Display the seed for reproducible diagnostics.
- Chunk validation must use the actual native controller envelope; supplied nominal movement values disagree with the port. User confirmed retaining native movement.

## Evidence

HUD/title checkpoint: commit 2ddcf26; complete existing suite and package gates passed. ROM SHA256 9d1ab0a798bddc932741badb17a7f975be2263baf1764507b84f85c61c589de9. Native busy-section slowdown remains. A ROM-pretransposed sprite experiment did not improve sampled cadence and was removed.

## Current playable checkpoint

M1 implementation reuses the original native stages and movement. Tested: Home entry without spending credits, eight independent seeded streams, persistent 180–600 second clock, pause/gate behavior, kill time/XP, C Hourglass with player movement, death penalty/respawn, sixteen stage transitions, terminal zero clock, Results bank-once, and new random seed for the next run. XP is visible in the fixed Window HUD.

This checkpoint is not the completed roguelike. Affixes, generated chunks, the full economy/gear/relic systems, special Dungeon bosses, persistent SRAM profiles, co-op, and pacts remain subsequent milestones. M0's corrected palette map is generated and checked; migrating gameplay art into those channels is part of the next graphics integration. M1 still uses native gameplay colors except the protected clock entries. M1 XP is a temporary one-per-native-kill placeholder pending M2 TP rewards. Banked XP currently survives runs in RAM, not a power cycle.
