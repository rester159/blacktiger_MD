# Native FM music adaptation

Hardware source: MAME `src/mame/capcom/blktiger.cpp`,
https://raw.githubusercontent.com/mamedev/mame/master/src/mame/capcom/blktiger.cpp
Two YM2203 devices at 3,579,545 Hz; audio CPU memory E000–E003 maps their ports.
The supplied `bd-06.1l` is used only by the offline observation tool.

Sound initialization selects prescaler 2D. Timer A registers 24=CE,25=01 give
(1024-825)*72=14,328 chip clocks per music update. IRQ handling calls 039F.
The six music channels occupy C100–C21F. C013 parity controls alternate updates.
Fixed main-code 233B–2340 selects round+21, covering eight round tracks.

`music_oracle.lua` isolates the audio CPU, captures FM port writes and waits for
an exact channel-memory/register-state repeat plus C013 parity. Each trace includes
boot/program selection at tick zero, its intro and complete periodic body. The
extractor maps six FM voices to YM2612 ports, remaps key-on channels, preserves
frequency latch ordering and corrects frequency numbers by 14/15 for NTSC. It
removes only redundant state writes; key events and necessary frequency latch
writes remain. Registers describing arcade timer/SSG hardware are not runtime data.

Carrier-only total-level attenuation adds 12 steps for output headroom. Carrier
masks in physical register slot order are 8,8,8,8,12,14,14,15 for algorithms 0–7;
algorithm changes recalculate affected levels. The slot-order mapping and output
routing are independently visible in the pinned Genesis Plus GX ym2612.c
SLOT1/2/3/4 definitions and setup_connection(). Modulator levels are unchanged.
Unattenuated output clipped in three four-second samples; adapted samples have no
clipped PCM samples. This does not prove every musical moment's mix headroom.

Native `music.c` interprets timed register records, not original instructions.
Its NTSC accumulator is exactly 7467/1791 source ticks per physical display frame.
PAL uses 308939/61461, within 1e-9 of the ratio derived from 53,203,424 master clocks,
3420 clocks/line and 313 lines/frame. PAL pitch gets a separate 33070/32768 scaling.
Genesis Plus GX system.h/system.c provide the pinned clock reference.

Remaining: boss/jingle selection, original sound priorities and resume behavior,
SSG-to-PSG effects, detailed listening/timbral comparison, PAL cartridge testing,
and real-hardware audio. The current game intentionally retains provisional PSG
SFX alongside the eight adapted FM round tracks.

Death's 1F command addresses sound special FF01, stopping SSG effects rather than
FM music. Native round music therefore continues through DEAD and restarts when
PLAY resumes, matching the round-start command being sent again.
