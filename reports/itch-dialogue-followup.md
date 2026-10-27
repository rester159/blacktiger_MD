# Itch feedback review — 27 October 2026

Reviewed both comment pages at https://rester159.itch.io/black-tiger-md and https://rester159.itch.io/black-tiger-md/comments?before=15.

## v1.9.5 release validation

The fixes below are included in v1.9.5, including the title-screen stamp. All 194 Makefile test recipes passed (source-oracle regeneration excluded). The old arena-parallax test assumed dialogue still owned BG_A rows; it was updated to verify full backdrop scrolling and fixed-position dialogue sprites, then passed on rerun. Strict `tools/package.py` also passed; it now requires the new contact/sound regression report.

Release BIN: `dist/blacktiger_MD_v1.9.5.bin`, 4,194,304 bytes. SHA256: `1441cd39a1a3d04c19fc8cc3fcc1de83079af10dd17b2c607063ed05931e467e`. Title capture: `reports/v195-title.png`. Stack margin remains 374 bytes in both sampled profiles. Physical hardware remains untested. No itch devlog was requested.

## Later v1.9.4 follow-up: four confirmed defects

Source: https://itch.io/post/17726092 (27 October 2026, 11:12 UTC). This section supersedes the earlier dialogue-fix assessment below; the earlier test checked text integrity but missed transparent scenery.

- Dialogue: BG_A carried both far scenery and text. Skipping scenery writes protected the text but cleared the window tops. In parallax Rounds 5/7, dialogue now uses sprites with source transparency, ahead of actors in the SAT. It temporarily reserves 128 actor-cache tiles, releases/invalidate caches at exit, and leaves BG_A and its scroll intact. All nine source dialogue pages require at most 32 sprites; actual scanlines stay within 16 sprites / 256 pixels in all 14 encounter fixtures.
- Snakes: source bank 2 template B732 has contact selector 0x26 and zero immediate damage. Fixed-ROM dispatch table 4751 routes selector 0x26 to 481C, which applies poison / consumes an antidote before hurt handling. The port omitted that callback. Restore `status_poison_contact` at sentry contact; keep arcade zero immediate HP damage. Poison disables dagger launches; antidote and exploration behavior stay intact.
- Rocks: source bank 4 B39F emits 0x3B when the rock starts falling, the same cue as player vertical falling. Replace the legacy attack placeholder with that native command; stop the sustained cue with 0x1F at first impact. Existing impact cue is otherwise unchanged.
- Bonus doors: life restart preserved `bonus_consumed` but cleared `bonus_entered`, reopening artwork without reopening access. Preserve the visual latch whenever a used trigger survives restart; fresh rounds still reset it.

Validation:

- Each new check fails against the published v1.9.4 ROM and its matching symbols: missing parallax rows, absent snake poison, absent isolated rock falling cue, reset door latch. The first rock fixture also triggered player falling and was corrected to hold the player stationary before accepting the negative result.
- Final candidate passes 16 targeted scripts: dialogue, bonus runtime, new contact/sound follow-up, boulder source/runtime, sentry source/runtime, status, bonus source, sprite line budgets, shop/dialogue priority, Round 5 parallax, Round 7 windows, actor contracts, SFX source comparison, and stack margin.
- Dialogue: all 14 native NPC contact/sequence fixtures in Rounds 5/7; full scenery-map VRAM, scroll, glyph patterns, SAT coverage and hardware line limits, completion/shop exits.
- Doors: deaths inside and after leaving bonus rooms in Rounds 1–6, plus wrapped Round 3 contact path; native entry, exit, persistence and rendered map checks.
- Snake: poison without an antidote, antidote consumption, and exploration immunity. GPGX and PicoDrive pass. Rock command reaches the native SFX player in both cores; source-matched host test checks start and impact stop independently of player motion.
- PicoDrive Round 7 captures include initial transparent page and two text pages; windows remain intact. No physical hardware validation and no full controller-only playthrough.
- Sampled stack margin: 374 bytes for both NTSC and PAL-ID with 60 Hz timing; unchanged from the previous release. This does not establish modified-console compatibility.

Candidate SHA256: `7cfc48f75088f8dc8c0041b6930004c85664686777770d0e48b2659bf56fdde9` (4 MiB). Local file: `dist/blacktiger_MD_v1.9.4_feedback_test.bin`. Build remains stamped v1.9.4; not uploaded, versioned as a new release, committed or pushed by this follow-up.

## Earlier review (historical)

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
