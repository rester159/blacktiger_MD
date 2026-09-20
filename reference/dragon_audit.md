# Pending native dragon family

Source aggregate e54221c17ce6b5ee4b98c63205f02d6a14ad9c2532b52263be9a25335700d30e.
These are source-reading notes, not a completed implementation or validation claim.
All addresses hexadecimal. Bank 3 unless identified as fixed.

## Construction and rendering

Constructors 8000/991D/9B24 copy 48-byte templates 8045/9962/9B69 to FAA0,
call fixed 59B2 boss entry, set E90D=3, display FF44, persistent primary OR 1.
Categories 28/29/30; initial/reset HP 80/120/100; layers 3/6/8; damage 2/3/5.
Mode 24, facing left, shared initial cursor 8364 (first frame 8369), hit cursor 836F.
Body bounds 32x32,32x32,16x24; weak boxes: offsets(0,0),bounds32x32 for first two;
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
Additional callbacks discovered in graph:9AD7,9AA9,9CE6,9CB8 (not yet audited).

## Layer breaks and defeat

9715 decrements layer. Nonfinal: call5D6D, active80, reset HP by category,
+27=3, keep mode (OR0); recoil left97A1/right983A, ends by calling8215.
Final: call5D6D, score task05/70, primary OR2, call5A38,
death root left98D3/right98F8. Exact score from fixed lookup still needs extraction.
9778 queues task08/2BB4 and sound3F, continue+3.
978E continues+3 while Ylow<112; otherwise skips an additional3 bytes to final
150-tick stationary frame then callback fixed5A4F (round clear).

## Suggested graph seeds

8369,8374,838E,83A0,83B2,83BD,90C5,87AB,9B07,9AED,979E,
97A1,983A,98D3,98F8, plus all 3*4*16 decision table pointers and 16 aim pointers83C8.
Intern continuation record+3 for callbacks that can fall through. Initial traversal
without defeat roots produced79 segments; not yet a complete graph.
Native actor implementation, independent source oracles, 128x64 renderer, projectile
family, collision and real cartridge integration all remain to be done.
