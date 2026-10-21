# Post-v1.8 itch feedback follow-up

## Changes

The terrain upload batch is reduced from 32 tiles (1,024 stack bytes) to 24
(768 bytes). Its scoped lifetime from v1.8 is retained. Instruction-level
sampling across cold boot, 900 attack refreshes and transitions through all
eight rounds measured the lowest stack pointer rising from `0xf674` to
`0xf774`. With heap end `0xf5fe`, the observed margin increases from 118 to
374 bytes. This is a robustness improvement, not a reproduced fix for the
reported hardware corruption. Sampling does not prove the worst-case stack
bound.

The new stack regression checks both normal NTSC and a PAL hardware ID with
60 Hz VDP timing in the pinned Genesis Plus GX core. That mismatch is a
software test scenario, not a simulation of the electrical modification.

## Round 8 lower healing wall

The wall at (1920, 712), persistent row 46, can be opened from the adjacent
pole. At player position (1880, 708), tap Up to grab the pole, then release Up
and attack facing right. The player settles at (1880, 704); five attacks open
the wall. Continuing to hold Up moves the attacks above the lower wall.

`tests/test_round8_hidden_input_runtime.py` verifies this with normal movement
and weapon logic after injecting the nearby initial position and selecting
the target actor. It checks all five hits and the terrain-open bit. It does
not establish a complete route from the round start or collect the reward.
The broader hidden-wall test separately checks reward collection using an
injected contact position. No wall placement, collision or hitbox was changed.

## Public page

Corrected the copyright paragraph from “Side Arms MD” to “Black Tiger MD”
on the live itch page and verified the saved result. No public comment was
posted, and no ROM was uploaded.

## Still unresolved

- Xaviersaverio's v1.8 fire-triggered corruption on a PAL console modified to
  60 Hz with Mega EverDrive Pro: https://itch.io/post/17657417.
- Older Genesis Model 3 compatibility report.
- Full natural traversal and collection of the Round 8 lower healing secret.

The user has no hardware access. Genesis Plus GX and PicoDrive can exercise
software behavior, but cannot establish that the physical-console reports
are fixed. Do not describe this candidate as a confirmed compatibility fix.
The published v1.8 binary is preserved; the candidate retains the v1.8 title
stamp and is distinguished by its filename and SHA-256.

## Final validation and package

- All 189 Makefile test recipes passed, using the existing source oracle
  captures. `prepare_source_data.py --all` was not rerun; this is not a claim
  of a fresh complete `make test` oracle capture.
- Strict `tools/package.py --name blacktiger_MD_v1.8-hwtest1.bin` passed.
- Separate Genesis Plus GX and PicoDrive cold-boot/900-fire-refresh smoke
  checks passed. Neither emulator reproduced the reported screen corruption.
- Candidate: `dist/blacktiger_MD_v1.8-hwtest1.bin` (4,194,304 bytes).
- SHA-256: `87f8d0b41b23819646ee49483e0fa39deab7e44d21d1990327e2404d2cc39006`.
- Baseline v1.8 binary remains byte-for-byte unchanged. Its original build
  report and symbols were archived alongside it before candidate packaging.
- No full human playthrough, hardware validation, commit, push or ROM upload.

Reproduce the extra core check with:

```sh
.venv/bin/python tools/smoke_core.py --core /path/to/picodrive_libretro.dylib
```

The harness supports the tested macOS word-swapped RAM layouts of Genesis
Plus GX and PicoDrive; other core layouts are not validated.
