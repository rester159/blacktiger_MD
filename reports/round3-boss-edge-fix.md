# Round 3 boss-room edge regression

Reported by homerhomer: https://itch.io/post/17672424

Confirmed on the exact released v1.9 ROM (SHA256 `4908cd8e7a90ae113feea9af71b9148275efe0e689c881efecb42c79bf5b39a8`). Holding Jump + Up + Right at the right arena boundary repeatedly restarted the jump, raising the hero 345 pixels from Y=1568 to Y=1223. The camera followed the hero; the dragon's camera-relative movement could follow it upward and leave the normal arena view. The source boss did spawn in the reproduction. A separate failure to spawn before any edge jumping was not reproduced.

The arena clamp changed the public player X without correcting the native movement controller's logical X. The next update interpreted that mismatch as a teleport and reset movement, including jump/gravity and held-button history. The fix synchronizes the controller's horizontal origin after arena clipping, preserving vertical movement and input history. No terrain, boss placement, or boss AI changes.

Fixed ROM: `out/release/rom.bin`, SHA256 `1111651e1825d0fb8ccaa7a89e553774d757f5798b837b3b8a690fb586ab1f76`. This was the development fix before the v1.9.1 version-stamp update; see `reports/v1.9.1-release.md` for the release artifact.

Regression: `tests/test_boss_edge_jump_runtime.py`, included in `make test`. Initial position is injected near each encounter; actual source boss spawning and subsequent controller movement are used. Both Round 3 edges, Round 3's negative vertical map lap, and both Round 5 edges are covered. The Round 3 jump rises 55 pixels, lands, and leaves the boss active and intersecting the viewport. This is not a full level playthrough.

Focused checks: boss edge jump, boss arena, boss terrain, Level 3 corridor, source player motion, runtime player motion, controls, dragon runtime (including damage/death/clear), and waveboss runtime. All passed. The new edge regression also passed in PicoDrive. No physical-console test was available.

Evidence: `reports/boss-edge-jump-v19-failure.txt`, `reports/boss-edge-jump-gpgx.json`, `reports/boss-edge-jump-picodrive.json`, and `reports/boss-edge-validation.json`.
