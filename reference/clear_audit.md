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
