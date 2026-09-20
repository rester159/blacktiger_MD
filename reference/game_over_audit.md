# Game-over and continue contract

Fixed ROM 20A4 selects game-over music 31. At 20B0 it passes seven to
033E, whose loop yields 60 updates via 0320: 420 total. Continue is enabled
by the arcade DIP switch and skipped for the post-ending round. The Genesis
port offers free continues after ordinary last-life exhaustion.

20DB selects music 34. The loop at 20EC reads ten numeral records from bank
6 B888 in descending order. For each numeral, 20FD repeats 25 times; 2160
yields three updates through 0308. This makes 75 updates per digit and 750
updates for the full offer. Input is polled once per three-update interval.
The last valid poll is 747; a new press after it cannot extend the offer.

The arcade checks credits at 2103, accepts held Start at 210B, decrements
credits through 0528, restores configured lives at 2118, and zeroes the
selected player's score digits at 2124/2140. Other progression fields pass
through the existing life-restart path. Native console continues omit credit
accounting; Start is available throughout the offer. Only score and lives are
reset at acceptance; the established restart path restores armor/HP and
retains equipment, inventory, consumed objects and world changes.

`tests/test_game_over.py` pins the control-flow bytes in the supplied source
and checks native durations, digit order, polling edges and continue cue.
`tests/test_game_over_runtime.py` exercises final-life depletion, every digit,
held Start, expiry, music, and new-game reset in the linked cartridge. Existing
restart tests verify persistent inventory and collected world objects.

Scope limits: these waits exclude the arcade task queues, fades and text
resource transitions around the notice/offer. The native screen uses the
existing Genesis text renderer and hides gameplay sprites during the notice
and offer; the arcade tears down its gameplay tasks/objects at 2040–2071. Source high-score entry, two-player switching
and arcade credits/DIP configuration are not reproduced by this module.
