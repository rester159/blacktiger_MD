# Native dragon family audit

Source aggregate e54221c17ce6b5ee4b98c63205f02d6a14ad9c2532b52263be9a25335700d30e.
Source-reading notes and verified implementation boundaries; full natural gameplay remains unverified.
All addresses hexadecimal. Bank 3 unless identified as fixed.

## Construction and rendering

Constructors 8000/991D/9B24 copy 48-byte templates 8045/9962/9B69 to FAA0,
call fixed 59B2 boss entry, set E90D=3, display FF44, persistent primary OR 1.
Categories 28/29/30; initial/reset HP 80/120/100; layers 3/6/8; damage 2/3/5.
Mode 24, facing left, shared initial cursor 8364 (first frame 8369), hit cursor 836F.
Body bounds 32x32,32x32,16x24; weak boxes: offsets(0,0),bounds 32x32 for first two;
third offsets(0,-24),bounds12x12, weak X becomes -56/+56 facing left/right on engagement.

Fixed loader 3D8C/3DAB uses standard five-byte animation records, callback 00,
single jump FF, retirement FE. 32 tiles, eight columns and four rows; horizontal
flip reverses columns separately within each row. Shared compile_clip is suitable.
VX 80 holds both velocities; VY 80 independently holds Y. Motion has no ordinary
small-actor offscreen retirement. Fixed 3EF6 conditionally calls 080A before motion
using engagement(+24), facing and screen X bounds; inspect 080A and later collision
code before implementing weapon/contact semantics. Rendering code continues past 4230.

## Shared body controller

8075: byte(playerX+48-actorX)<96 starts root8374, else next record+3.
8093: mode24, hit cursor9799, engaged(+24)=1; category30 weakX=-56; continue+3.
80B4: decrement +27 if nonzero; when result=1 restore mode24. Dispatch category29
9992/category30 9B99, otherwise category28 80D3.
All profiles: screenY high nonzero ->8190; Y>=112 ->8194.
8190: high FF ->81A4 downward root(left83BD/right83B2); other high ->8194.
8194: upward root left87AB/right90C5.
Decision: adjustedX=screenX+(left?0:128). If high!=0 compare adjustedX and playerX
with both high bytes incremented; flip facing toward player, reset +25=0,
select right turn838E/left turn83A0. Third profile also updates weakX +/-56.
Otherwise weighted choice alternates +25, chooses one of two tables per direction,
then indexes (E009&15). Pair bases left/right: category28 82E1/82E5,
category29 9A21/9A25, category30 9C30/9C34. On old +25=0 set1 and use second pointer;
else set0 and use first pointer.
8178: if Y high0 and Y>=112 decide80B4; otherwise continue+3.
81B4: if adjustedX high!=0 enter turn check80F9; otherwise continue+3.
81D1 toggles +25 then decides80B4 (so decision toggles again).
81E1: only attempt fire if Yhigh0,16<=Y<176, X+(left?0:112) high0,
and E009 bit0=1. Otherwise continue+3; successful condition ->8215.
8215 aims with fixed05B2 from X+(left?0:112), restores X. Right-facing direction:
if >=7 clamp to6 for <16 else31, then index ((direction+1)&31) into83C8.
Left direction clamp10..17 then index(direction-10) into83D8.
828F calls projectile constructor9D33 then continue+3.
8299 category28 ->81D1; others increment aim direction, clamp right result>=7 to5,
left result>=18 to17, then828F.
82C9 category28 ->8215; others use left9AED/right9B07.
9AA9/9CB8 select one of three distance roots (byte absolute playerX-actorX;
thresholds32/96), separate left/right pointer triples at9AE1/9AE7; identical9CF0/9CF6.
9AD7/9CE6 launch seed A109 then continue+3. Critically, direct callbacks9992/9B99
select their own decision tables even when the actor category differs; common81B4
turn check branches80F9 and uses category28 tables if no turn is required.

## Layer breaks and defeat

9715 decrements layer. Nonfinal: call5D6D, active80, reset HP by category,
+27=3, keep mode (OR0); recoil left97A1/right983A, ends by calling8215.
Final: call5D6D, score task05/70, primary OR2, call5A38,
death root left98D3/right98F8. The fixed score lookup gives 1,000 points.
9778 queues task08/2BB4 and sound3F, continue+3.
978E continues+3 while Ylow<112; otherwise skips an additional3 bytes to final
150-tick stationary frame then callback fixed5A4F (round clear).

## Suggested graph seeds

8369,8374,838E,83A0,83B2,83BD,90C5,87AB,9B07,9AED,979E,
97A1,983A,98D3,98F8, plus all 3*4*16 decision table pointers and 16 aim pointers83C8.
Intern continuation record+3 for callbacks that can fall through. Initial traversal
without defeat roots produced79 segments; not yet a complete graph.
The native body controller in src/dragon.c now matches 427,140 independent source
ticks in 384 cases and 2,625 launch snapshots. The collision loop gates hits by mode,
not actor 80/40 state; pre-engagement hits can retain 40 after mode returns to 24.
The native hit gate and manual-hit oracle preserve this behavior.
It accepts a projectile-launch callback so the projectile owner controls allocation.
The cartridge now calls it for all three original boss placements, renders 32 sprite
pieces, dispatches native projectiles and checks source-derived wide collision.
Runtime tests verify both weapon types, all layers, natural attacks, rewards and clear
callbacks. Original palette changes, health display and full cutscene timing remain gaps.

## Projectile continuation notes

9D33 orbs: 16 roots from pointer table9E26, constructor stores cursor (start at+5).
Body sets alternate(+25) to vertical launch offset before allocation, even if full.
Right direction index=(dir+1)&31: Y offset16/24/28 for index<3/<5/else.
Left index=dir-10: offsets28/24/16. X offset0 left/112 right. Template9DD6,
HP1,damage1,bounds6x6, mode8. Terrain callback9E46 probes(8,8), enters deathA079
with mode11 on solid; otherwise continue+3. Callback9E69 allocates medium explosion
from48-byte template9DF6 at orb(-8,-16), then orb rootA093 on success or continue+3
on failure. Explosion callbacks9EC7->mode9,9ED0->mode27; both continue+3.

A109 seeds: templateA170, mode11, immune, no contact. Initial cursorsA1A1 right,
A1DF left; spawn X+86/right or+22/left,Y+16; copy bodycategory into seed+10.
A190 probes(8,8); solid callsA222 and continues+3; empty continues+4 (skips FE).
A222 allocates six-part group from templatesA397(category29)/A457(category30).
Group positions and floor search match existing container_wave_spawn: firstthree
seedX+48/right or-32/left, nextthree another+24/-24; test terrain(8,16) at screenY
112,128,...192 (six probes), fallback playerY+16. All groupY same. Category30 middle
parts contactcodeAB (43, reversed controls); category29 ordinarydamage1.
Wave callbacks A517 moveX +/-48 thencontinue+3;A535 mode9 thencontinue+3;
A53E sound9 thencontinue+3. These match the existing container trap controller events
3/4/5; both profiles are now extracted into container_segments and use dragon_wave_spawn.
Their 5,760-tick oracle checks graphics, movement, contact mode, and retirement; native
contact return distinguishes ordinary damage from reversed controls. The source wave
constructor ground search and pool-group allocation still need dedicated validation. Fixed allocator0412 uses return-address skipping at03C5 on
success; the following unconditional JP is the failure path, not dead allocation code.

## Verified projectile and collision integration

Native src/dragon_shot.c uses 44 compiled segments for 16 orb directions, two seed
directions and the medium impact explosion. Source tests compare 33,120 ticks including
available/full secondary pools, 8,560 explosion ticks and 444 active-wave snapshots.
When the medium pool is full, source FF/A079 reads callback bytes as a raw frame:
duration0,code469,palette6,flip1,VX1,VY-110. The loader uses a 256-tick byte countdown.
The compiler resolves that frame offline; an exhaustive 16-bit Y proof shows retirement
within 8 ticks, so later misaligned records are unreachable. Native animation supports
the zero-duration counter without executing source instructions. The oracle exercises
36 such zero-countdown frames. Small native projectile capacity and shared source
actor-pool contention remain distinct from these isolated full-pool checks.

Wide collision routines435B/4463/4550 use weapon X origin 56, player X origin 48.
Normal player Y subtracts 16; alternate posture adds 26 and uses body bounds 3x3.
Dagger weak-Y subtraction retains carry from subtracting the signed weak offset;
other dragon axes clear it. The native shared geometry helpers match 31,200 source
cases across all three templates, both final-dragon weak-X offsets, both weapons,
normal/alternate postures and unsigned screen-coordinate edges. Native player posture
and chain extents still await the exact player controller port.

Orb contact handler fixed48F7 allocates the same medium explosion at playerX/playerY,
then sets the orb cursorA08E with remaining1 so it retires next tick. It does not
directly damage the player. Native contact now preserves that conversion and current
frame. On full medium-pool failure, the source advances its current animation pointer
by3 and subsequently reads misaligned frame bytes. The native port deliberately
discards that orb without damage instead; cartridge tests verify both available/full
contact outcomes. This is distinct from the correctly traced full-pool terrain/weapon
impact path at9E69, whose zero-duration frame is preserved.
