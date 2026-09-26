# Native front end and start presentation

The title logo is the supplied arcade board's frame 600 captured by the normal
MAME boot. `run_title_oracle.py` writes its PNG and source/trace identifiers;
`build_ui.py` retains logo geometry and reduces RGB444 to Genesis RGB333, with
four tile palette lines. The native menus replace the old GAME OVER/INSERT COIN
region. This is original artwork with new mode selection, not a claim that the
arcade had Home/Boss Rush menus.

`intro_oracle.lua` inserts one coin at update 600 and presses Start at 650, then
records the board's scroll RAM, character RAM, palette RAM and sprite RAM every
update. The read-only share API follows MAME's documentation:
https://docs.mamedev.org/luascript/ref-mem.html
`intro_oracle_events.txt.gz` is losslessly compressed; its manifest hashes the
uncompressed trace. `build_intro.py` compiles the palace, dragon sprite blocks,
palette flashes/fades and character changes into native typed events for source
updates 708–1549 (842 updates). Original program instructions are never shipped.
The original start music command is 0x30. Genesis palette 0 holds palace colors,
1 dragon colors, and 2 the three used text palettes. Sprite textures upload only
when they change. Both normal-game modes enter this presentation; a new Start
press after 30 updates skips it. Continues and Boss Rush go directly to play.

Arcade stores its coin bank separately from Home's limited run credits. In v1.2,
Start is the coin input inside Arcade, and A selects Play and accepts continues.
Each new Start edge plays the original FM command 20 (fixed 0A3A), before the
coinage meter awards a credit. The original cap is nine (0A62–0A6B), and the
source CREDIT label is at 16FA. The original title capture places CREDIT at
column 23, row 27, with its single digit at column 31. The native title follows
that position; gameplay and shop use the original currency HUD without a credit
overlay. Home balances above nine retain two digits. Coin sound temporarily takes the FM player; after it
ends the previous gameplay track restarts. It remains audible with Music OFF
and Sound FX ON. C/Mode cannot add credits. Home retains Start and its configured
credit budget, defaulting to the initial game plus two continues. DIP/Options
share lives, difficulty, coinage, allow-continue and music/SFX controls. Difficulty
currently selects source bank 6 B6F0 weapon damage plus the existing source shop
price table; remaining original difficulty effects and physical cabinet DIP
functions are not yet fully reproduced.

Boss Rush runs the original eight native boss families in their source order,
in a flat collision arena using round-eight palace artwork. It disables ordinary
spawn scanning and bonus doors. Victory pays 1000 + 500*boss_index Zenny once,
heals the player and enters the ordinary shop, including after the final boss.
Leaving the shop resets boss-specific transient state while retaining inventory,
Zenny and lives. Death and paid continuation restart the current boss. Tests use
actual pickup-triggered fatal combat and death callbacks; they do not prove that
all bosses are balanced for a natural weapon-only run in this arena.

Gameplay scrolling now uses SGDK's VSync setters. HUD text and bars queue their
writes for VBlank too. `test_presentation_runtime.py` verifies complete old/new
views across 32 camera changes; it cannot test host compositor or monitor tearing.
