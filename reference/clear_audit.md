# Round-clear source contract

The offline MAME capture enters the original fixed-ROM routine at 5AAC after
the landing/ladder wait. It intercepts the scheduler yield at 0116, preserving
requested delays and sprite RAM. The two protection-only checks at 5BAB and
5C0B are bypassed before their stack pushes; the animation instructions remain
unchanged. Ordinary capture stops at 5C6E and final capture at 7B98.

The trace covers both armor branches and all five weapons. Unarmored ordinary
sequences last 227 updates; armored ones last 138. Final-round prefixes last
170 and 81 respectively. The initial unarmored update retains the prior hero
picture while granting armor level 2. Sprite coordinates wrap as source bytes.

A second capture executes 5CCC–5CEF for all eight reward-table rows and four
starting balances. The final row exists but is bypassed by the round-8 branch
at 5BC4; the native final reward is therefore zero. Rewards add to the 16-bit
binary Zenny balance, including wraparound. The original five-digit BCD display
is independently checked by extraction; the native HUD still formats its binary
balance. The common 032C scheduler helper establishes the 240-update bonus hold.

Only generated sprite records and reward constants enter the cartridge. Native
C implements clear progression; no original instructions are interpreted.
`tools/extract_clear.py` pins source/trace/Lua hashes and opcode witnesses.

Validation: `tests/test_round_clear.py` compares all captured animation updates
and native rewards; `tests/test_round_clear_runtime.py` checks linked cartridge
state progression, source-matched hardware victory sprites, airborne landing
and transitions. Existing boss tests cover production clear
entry. These are controlled subsystem tests, not a natural game completion.

Excluded: original bonus map and text resources, fade timing, final cutscene,
whole-board task scheduling, and dedicated source traces of landing/ladder wait.
The port currently shows its own text bonus panel over the level background.

## Bonus-screen graphics

`tools/clear_screen_oracle.lua` executes fixed 5C82–5CEF for all seven ordinary
rounds, then consumes the queued 1D–23 text request through the original 1429
handler. It initializes inherited global/round palettes from their source copy
lists, bypasses the 0300 scheduler yields, and captures background RAM, character
RAM and palette RAM. The source map copy at 5CA6 and all seven 512-byte bank-four
maps are independently checked during extraction. Captured setup is not evidence
of fade timing, full-board scheduling, or a natural completed round.

`tools/extract_clear_screen.py` decodes the captured maps through the pinned board
layouts, crops arcade rows Y16–239 and deduplicates 8×8 Genesis patterns across
all seven screens. The original two background palettes retain all opaque pens;
only RGB444-to-RGB333 channel truncation is needed. Transparent pen 15 becomes
Genesis pen 0. Character palettes 0 and 8 fit together in the third palette.
The existing console HUD keeps the fourth palette. The native current Zenny
balance replaces the captured sample balance with original digit glyphs.

The native renderer installs both maps with the display disabled, suppresses all
gameplay sprites, keeps the existing 240-update bonus hold, and rebuilds terrain
and palette/cache state on exit. Cartridge tests compare every visible map word,
all shared pattern bytes, all 48 palette entries, dynamic balance glyphs, hidden
sprites and the following round's rebuilt VRAM. Rendered captures were inspected.
The prior exclusion of bonus map/text assets above is resolved; fades, original
HUD, final cutscene and natural full-game validation remain unfinished.

Reproduction:

```
.venv/bin/python tools/run_clear_screen_oracle.py
make assets
make test
```
