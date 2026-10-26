# Round 4 column victory camera fix

The reporter observed the red imp victory sequence showing unrelated scenery when the boss died while the player hung from either column tier. Reported hardware: Mega Drive Model 2 VA0, Sega 315-5660 FC1004 GOAC, M68HC000FN8 CPU, Sega 315-5676 Z80 clone, Everdrive Evergenesis V3. This is the reporter's configuration, not a validation of this candidate.

The clear descent clamped the horizontal camera to 0..map_width-256 even though ordinary play maintains horizontal wrap laps. At player x=3064 (Round 4 x=1016 plus one 2048-pixel lap), camera x jumped from 2952 to 1792. The resulting scenery matches the reported stone structure. Player world x did not teleport; the camera and byte-sized victory screen coordinates made it appear so. Grounded clears bypass this descent branch.

The descent now uses the ordinary gameplay horizontal camera policy, including existing boss-room bounds. No movement, collision, boss, or music logic changed.

Validation:
- Released v1.9.2 ROM SHA-256 b5167379b22a90b4c347cbeb8b4af47bd32a34636f404db74e1a3a21b6a65d48 fails the new regression at camera x=1792.
- Candidate SHA-256 1bb5bca49c1e7a0fe8c069f070f89c788cce87fc9335b5446838e7f317f29b8e builds successfully.
- New test_column_clear_runtime.py passes both column heights (80,144), at laps -2048,0,+2048 in Genesis Plus GX and PicoDrive (fresh process per PicoDrive case). Asserts continuous horizontal camera/player relation, landing at y192, completed climbing/falling, victory screen position (112,144). Captures inspected.
- Existing test_round_clear_runtime.py passes all 20 weapon/armor/final profiles plus airborne landing, payouts and transitions.
- Existing test_hunter_runtime.py passes normal and Round 4 boss damage layers, death and clear cleanup.

Scope: injected column/clear states exercising native descent and rendering; not a full controller-only level traversal or a physical hardware test. The initial candidate retained version 1.9.2. The fix is now released in v1.9.3; see v1.9.3-release.md for final artifact validation. Released dist/blacktiger_MD_v1.9.2.bin is preserved.
