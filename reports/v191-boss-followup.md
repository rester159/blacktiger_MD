# v1.9.1 boss first-contact follow-up

User reports: Round 5/7 bosses become invulnerable after distant crouching dagger fire, in Arcade and Boss Rush. Reported hardware is Mega Drive Model 2 VA0 with EverDrive EverGenesis V3; also observed by the reporter in Kega Fusion 3.64 32-bit. Cartridge firmware, region and tested ROM hash were not supplied. The Round 3 dragon was also reported missing on the first arrival, then present after losing a life. These are reporter observations, not hardware validation performed here.

## Confirmed defects and fixes

- Wave-boss damage before proximity activation sets `Actor.state=1`. The activation callback resets mode and health but left this hit state set. Movement and attacks resume, while `waveboss_vulnerable()` rejects every subsequent weapon hit. Clear the actor hit state on activation. This preserves the existing activation health and layer counts.
- Round 3 wraps horizontally. Boss spawning correctly places the dragon in the current map lap, but the arena clamp used absolute source coordinates. On an injected wrapped first arrival, v1.9.1 moved the player from X=-144 to 584 (or 1904 to 928), leaving the dragon off-screen in the original lap. Project the arena boundaries into the current camera lap, matching actor placement. Also normalize Round 5's doorway entry check across horizontal laps.

The exact released v1.9.1 ROM was rebuilt with matching SHA256 `f022247708b5890d30695d7daf4bc9446cda63ee1007723097e7becf189660db`. New regressions fail on that ROM for early damage and both wrapped first-arrival directions (`reports/first-contact-v191-failures.txt`).

## Test scope

`tests/test_boss_first_contact_runtime.py` injects approach positions and a controlled head projectile to isolate damage before activation. It checks that both bosses accept subsequent hits through every layer and complete their encounter in normal stages and Boss Rush. Round 3 fixtures inject a first-arrival position in three horizontal laps and then let native spawning and gameplay run. No position correction, boss insertion, or damage injection occurs during the arrival checks. They verify continuous player position and a dragon intersecting the viewport.

These are targeted reproductions, not a full natural level route or a recreation of the reporter's exact crouching-fire photo (no photo was attached here). They confirm defects consistent with both reports. The Round 3 result does not establish that every possible missing-boss report has the same cause.

All seven new cases passed in Genesis Plus GX and separately launched PicoDrive processes. Existing checks cover the previous edge-jump fix, arena bounds and terrain, wave-boss source traces and damage/death, seeds, Boss Rush, horizontal wrap, Level 3 corridor, dragon combat and checkpoints. See `reports/first-contact-validation.json` and `reports/first-contact-picodrive.json` for results. No hardware testing performed here.

Development ROM SHA256: `0a46fc615ff8e7cec9f964ecd960e5548c1c7e5333ac86e066150933f4d10f32`. Version remains 1.9.1 for this unpublished development build. This investigation was subsequently included in v1.9.2; see `reports/v1.9.2-release.md`.
