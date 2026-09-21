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

## Native SSG effect programs

`tools/sfx_oracle.lua` isolates the original audio CPU and captures all 36 SSG
commands at all four C022 timer phases. Its 4,096-update ceiling covers complete
runs of 34 effects and prefixes of commands 14/3C. A separate full original-driver
capture, `sfx_long_oracle.lua`, proves that those two commands are finite phrases
repeated 255 times: they end at updates 35,956 and 17,341 in every phase.

`tools/extract_sfx.py` compiles original effect parameters into typed duration,
pitch, volume, noise and bounded-repeat records. Shared native C performs the
fixed-point ramps, byte wrapping, every-fourth-tick volume/noise updates, phrase
loading, repeat counting, source priority replacement and stop command 1F.
All 36 programs now share 5,112 bytes of parameter data instead of 87,114 bytes
of recorded register streams. No sound CPU instructions are linked or executed.

Pitch accumulators use 12.4 fixed point and signed byte increments; volume and
noise accumulators wrap as bytes. Zero/keep parameter cases preserve the original
asymmetry: zero volume silences output without clearing its saved accumulator.
A new phrase loads parameters and decrements its hold without applying a ramp
on that first update. Source loop counts are byte-sized, including wrap semantics.
The native NTSC/PAL timer accumulators advance across missed simulation frames.
Output remains updated at the audio/game cadence, rather than sub-frame scheduling.

The hardware adaptation follows the primary implementations:
[YM2203 prescale](https://github.com/mamedev/mame/blob/master/3rdparty/ymfm/src/ymfm_opn.cpp),
[SSG clock and amplitude](https://github.com/mamedev/mame/blob/master/3rdparty/ymfm/src/ymfm_ssg.cpp),
and the pinned local Genesis Plus GX `core/sound/psg.c`. At source prescale 2D,
tone periods map directly to NTSC Genesis periods; PAL periods receive clock
correction. Periods above the SN76489 ten-bit range clamp to 1023. Amplitudes map
to nearest PSG attenuation with 6 dB headroom. These are hardware adaptations,
not waveform equivalence.

The mixer selects the strongest tones across both source slots. Noise uses the
fixed divisor when possible; otherwise it reserves the third tone's clock and
leaves two audible tones. It selects the strongest noise contribution. Source
AND gating becomes additive, excess voices can be omitted, and noise polynomial,
timbre and low-frequency limits differ from the arcade hardware.

Audited production bindings remain player attack 3A (bank7 8B74), jump 1B (88EE),
and death's 1F stop followed by 02 (8524). Player attack has its own event, separate
from generic enemy attack sounds. The extra prototype clear chirp is suppressed
because the source FM cue is present. Other generic gameplay cues remain
provisional and cannot overwrite an active source effect. Further movement,
impact, NPC/shop/enemy bindings, original command-queue contention and detailed
hardware listening remain open.

`tests/test_sfx.py` compares 19,511 register-state batches against the original
144 command/phase prefixes in both regions. Another 5,908 original checkpoints
cover the full long programs, including each phrase boundary, private pitch,
volume/noise accumulators, slopes, loop count, remaining duration, program
position and termination. Priority, stop and explicit PSG chord/noise fixtures
are also checked. `tests/test_sfx_runtime.py` renders all 36 complete effects,
checks isolated and music-mixed peaks, finite termination, input-driven
jump/attack and timeout death without stopping FM. The preview WAV contains
adapted death, jump and attack samples; it is not an original arcade recording.
These checks do not establish natural full-game audio, complete event bindings,
waveform equivalence, or hardware/PAL listening quality.

## Ordered player controller commands

The shared native movement controller emits a bounded, ordered list each update.
Audio consumes it once before damage/death dispatch, avoiding the previous
single-event overwrite. Source bank 7 supplies jump `1B`, attack `3A`, ladder
attach `1E`, fall start `3B`, fall completion `1F,1C`, and moving-ladder `1A`
on the global 16-update cadence. Ordinary jump landing has no separate cue;
attack-jump entry omits `1B`. Catching a ladder during falling stops effects.

The refreshed source controller oracle captures its actual sound queue with
attract-mode suppression disabled and an explicit global frame counter. All
56,720 updates across 719 cases match native motion, attacks and sound output,
including 931 commands and multi-command updates. The cartridge check also
verifies ordered stop/landing consumption and no replay on paused frames.
This does not establish complete game-wide command scheduling fidelity.

## Shared native command buffer and damage/pickups

Movement output now joins a 16-command per-update buffer in Game. The native
handlers append commands in execution order; audio consumes and clears it once.
This prevents a later player event from overwriting an earlier command. The
buffer drops excess commands if full; it does not claim the original asynchronous
mailbox's producer/consumer timing or overflow behavior. Generic enemy/NPC/shop
placeholder events still use the old single-event field pending source matching.

Original ordinary damage dispatch at fixed 2F42 is silent when armor remains.
Exact break and overflow invoke 7A09, queuing `17`; surviving health damage queues
`01` at 2F93. Lethal damage marks death; the native immediate death initializer
then queues its separately witnessed `1F,02`. Original damage queue captures now
cover all 180 existing health/armor/damage/invulnerability fixtures, matching the
native ordered output (with that explicit death-entry suffix). Cartridge contacts
verify silence, armor break, health damage, death and protected hits.

Both placed time-extension and screen-attack items emit `05` on collection.
The 406-update item oracle now records and compares actual sound queues, including
empty queues before and after collection. This replaces their generic coin chirp.
