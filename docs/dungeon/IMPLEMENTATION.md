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

The first release reused all eight native maps unchanged. It did not deliver generation. This revision replaces those layouts with seeded source-slice assembly and restores gameplay art to the pre-HUD hero/enemy palettes. HUD palette pressure no longer requantizes the sprites. Dungeon uses the same arcade icon HUD as normal Play, with XP and Hourglass in unused bottom cells, scaled vitality plus its numeric value, and the persistent run clock in TIME. Background clock-color overrides were removed.

The build-time library contains 119 screen-wide 256×224 slices from all eight arcade maps. The native player controller certifies a walk/jump witness for each slice and replays every same-theme ordered pair without resetting motion at the seam. The resulting compatibility table is consumed by the runtime generator. A change to the controller rebuilds this library. Runtime stages use 6/7/8/10 slices by act, choose only compatible neighbours, independently randomize the source art theme and skeleton placements, and include two shop NPCs. Original graphics/collision data are referenced in ROM, not duplicated; no full generated map is allocated in RAM. Death respawns at the current slice's entry. Up at the far-right endpoint enters the boon gate.

Tests cover 10,000 seeds × 16 stages, 2,048 native-controller routes, and eight linked-cartridge joypad route replays with zero cache faults. The ROM routes suppress enemy spawns to isolate traversal. Original actor/NPC subsystem tests cover those routines separately; these tests do not prove full-run combat balance. The sprite atlas and palette match commit 4657999 byte for byte. Dungeon's live gameplay CRAM matches the corresponding normal-game source palette.

This is still not the completed roguelike or the full M4 generation milestone. Vertical/branch sockets, doors/keys, threat-point population budgets, affixes, all gear/relic systems, dedicated Dungeon bosses, persistent SRAM profiles, co-op, and pacts remain unfinished. The current spines are deliberately conservative horizontal routes. M0's restricted palette proposal is not used for gameplay; the user's correction prioritizes existing artwork fidelity. XP remains a temporary one-per-native-kill value and banked XP remains RAM-only. The 16-stage clock/lifecycle checks remain in place.
