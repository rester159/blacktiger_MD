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

## Event mapping and finite catalog

All25 FM programs at20–39 excluding control38 are captured. END records represent
all six source channel pointers becoming zero; unlike a repeated state they must
terminate, not loop. Native finite completion applies the final writes then keys
off all channels. The final ending program33 lasts19,365 timer updates.

Audited event mappings: fixed5A30 boss table29292A29292A292B; fixed6470 shop2C;
fixed6547 round restart after shop; fixed5A4F clear32/final33; fixed20A4 game-over31.
Fixed20DB has continue34; fixed21B7 uses2E; fixed51AE uses2F; bank6 B92B uses30;
fixed7079 alternate-area entry uses2D. Those latter contexts still require their
presentation/event ports. The entire catalog is available without inventing event
bindings. Boss requests are issued by the native spawn path and cannot be replaced
by the fallback round-music selection in the same frame.

## Native finite SSG effects

`tools/sfx_oracle.lua` isolates the original audio CPU, initializes its driver,
submits each of 36 SSG commands, and records register writes from the 0A50 update
routine at all four C022 timer phases. Commands 14 and 3C did not terminate or
repeat within 4,096 updates. Their bounded observations are retained, but they
are excluded from playback data; no invented timeout or loop is applied.
The other 34 commands have witnessed finite termination in all four phases.
An initial capture exceeded the runner timeout after a nonterminating-case
assertion; it was rejected and replaced by this explicitly bounded capture.

`tools/extract_sfx.py` emits 118 deduplicated streams (87,114 bytes) for 136
command/phase profiles. `sfx.c` implements two native effect slots, source priority
replacement, stop command 1F, source-rate timing and PSG output. Only timed data
is compiled; the original sound CPU program is never executed on Genesis.
The same NTSC/PAL clock accumulators as music advance effects across missed
simulation frames. Register updates are rendered at the audio/game update cadence,
not individually scheduled at sub-frame times.

The hardware adaptation follows the primary implementations:
[YM2203 prescale](https://github.com/mamedev/mame/blob/master/3rdparty/ymfm/src/ymfm_opn.cpp),
[SSG tone/noise clock and amplitude](https://github.com/mamedev/mame/blob/master/3rdparty/ymfm/src/ymfm_ssg.cpp),
and the pinned local Genesis Plus GX `core/sound/psg.c`. With source prescale 2D,
tone periods map directly to NTSC Genesis periods; PAL periods receive clock
correction. Values above the SN76489 ten-bit range clamp to 1023. Source amplitude
steps map to nearest PSG attenuation with 6 dB headroom. These are adaptations,
not waveform equivalence.

The mixer selects the strongest available tones across both slots. Source noise
uses the fixed divisor when possible, otherwise reserves the third tone's clock
and leaves two audible tones. It selects the strongest noise contribution;
source tone/noise AND gating becomes additive and excess voices can be omitted.
Noise polynomial/timbre and low-frequency limits remain hardware differences.

Audited production bindings are player attack 3A (bank7 8B74), jump 1B (88EE),
and death's 1F stop followed by 02 (8524). Player attack now has a separate event
from generic enemy attack sounds. The invented clear chirp is suppressed because
the source clear FM cue is already present. Other generic gameplay effects remain
provisional; while a source effect plays, the old fallback cannot overwrite it.
Further movement, impact, NPC/shop/enemy bindings, the two sustained programs,
original command-queue contention, and detailed hardware listening remain open.

`tests/test_sfx.py` compares 5,120 native register-state batches with the source
across all 136 profiles in both regions, including completion, priorities, two-slot
operation, stop, rejected unsupported commands, and explicit PSG chord/noise
fixtures. `tests/test_sfx_runtime.py` renders all 34 effects through the cartridge,
checks isolated and music-mixed peak levels, finite completion, input-driven
jump/attack, and timeout death without stopping FM. `reports/sfx-preview.wav`
contains adapted death, jump and attack samples. These are not source recordings
or natural full-game audio verification.
