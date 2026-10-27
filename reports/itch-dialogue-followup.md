# Itch feedback review — 27 October 2026

Reviewed both comment pages at https://rester159.itch.io/black-tiger-md and https://rester159.itch.io/black-tiger-md/comments?before=15.

## New reproduced issue

ZeroVolt confirms the Round 4 column victory fix in v1.9.3, but reports that Round 7 windows still distort during old-man dialogue. The earlier comment also confirms the v1.9.2 Round 3/5/7 boss fixes.

`arena_video_restore` queued backdrop rows 6–9 for DMA while `overlay` wrote dialogue into those same rows immediately through the CPU. The queued scenery subsequently overwrote the text. Rescue mode fixes those rows at zero horizontal scroll, so the overwritten window fragments appeared at the wrong horizontal position until another dialogue page or gameplay restored the map.

The restore routine now leaves the four dialogue-owned rows alone during rescue. Other scenery keeps its normal scroll. Dialogue completion restores all backdrop rows normally. This also covers Round 5's mountain backdrop.

Regression: tests/test_dialogue_backdrop_runtime.py covers all 14 source NPC placements in Rounds 5 and 7, using injected proximity followed by native spawn/contact, complete dialogue, rewards/shop exits and scroll restoration. It checks dialogue VRAM against current source-derived page glyphs at stable frames, including the initial page before text appears. The released code fails the Round 7 row 5 case at tick 8 with scenery tile 0x02bc where dialogue tile 0xe580 should be. The fixed code passes all 14 cases. This is not a complete controller-only traversal.

## Other comments

- Model 3: a later reporter comment confirms v1.8 and v1.9 boot, superseding that reporter's earlier failure. This is external confirmation, not our own hardware test.
- PAL console modified to 60 Hz with Mega EverDrive Pro: the latest failure report is still for v1.8. The previous memory fixes and emulator coverage do not prove this physical configuration is fixed. No new cause is established; leave this unresolved rather than make another speculative compatibility change.
- Older NTSC EverDrive and BlastEm reports lack a current-version reproduction; remain unverified.
- Chest flames following jumps, invisible idle weapon, shop bats/owned weapons, audio balance and remaining-lives notice are covered by the v1.8 fixes and existing tests.
- Earlier shop text/prices, dialogue sprite priority, saves/high scores, boss areas and enemies have existing fixes and regression coverage; no new regression is reported in those threads.
- Round 8 lower hidden wall has the existing input-driven pole attack test. Round 2's alleged missing rock remains skipped per the user's prior instruction: all five source placements are present.
- Graphics wishes and requests for other ports are not new reproducible defects.

Version remains 1.9.3; this is an unreleased fix. No itch comment, upload or Git push was made in this review.

## Candidate validation

- ROM SHA-256: `102c3441b1c47276789672cf3b882748ec38d2b0a80c80443a5af2effe39f01b` (4 MiB).
- Test BIN: `dist/blacktiger_MD_dialogue_fix_test.bin`; title still reads v1.9.3. The published v1.9.3 BIN is preserved.
- All 14 encounter fixtures passed in Genesis Plus GX. Rebuilding after the baseline comparison produced the identical ROM hash.
- PicoDrive: visually inspected a controlled Round 7 dialogue-entry capture with correct text and no displaced window fragments. This was a separate visual fixture, not the full 14-case VRAM test.
- Existing NPC source-contract, all-eight-variant NPC runtime, backdrop scrolling, shop/dialogue sprite priority, arena parallax and stack-margin scripts all passed on the final candidate. Stack tests include NTSC and PAL-ID/60-Hz scenarios, not a physical mod simulation.
- Added the encounter regression to `make test` and the strict packaging gates. Full release-suite/packaging was not run for this unreleased candidate.

The user subsequently requested publication and a version bump. The fix is released as v1.9.4; see [release validation and publication](v1.9.4-release.md).
