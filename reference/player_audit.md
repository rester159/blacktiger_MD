# Shared player controller

Source set: e54221c17ce6b5ee4b98c63205f02d6a14ad9c2532b52263be9a25335700d30e.
Source fixed 1E17 selects bank 7 and enters 8000. Native C executes no Z80 instructions.

## Implemented locomotion

`src/player_motion.c` covers bank 7 input decoding 80C3–8101, walk/crouch/ladder
8625–87FF, jump 8800–8AE9, falling 8F8D–9084, ladder attach/detach 8F3C–8F8C,
and logical camera integration 8126–81EE. Terrain helper fixed 06C8 distinguishes
0 empty, 1 ladder, 2 platform, 3 solid. Both 2 and 3 stop motion; only 2 selects
platform-assisted jump. Probes are at the source coordinates, before integration.

Motion state names correspond to the source's meanings, not an emulated RAM array:
scroll_x/y=E030/32, screen_x/y=F401/403, jump_origin=E913; signed integer vx/vy=F406/407;
fraction=F40A; subtick=F40F; pose=F411; jumping/jump_request/direction/redirected=
F412–415; camera_return/below_origin/falling/ladder=F416–419; low=F426; frame=F427;
selector/previous=E901/902; idle=E907; jump_history=E903; screen_motion=E054.

Gravity adds 64 to the 8.8 velocity; position integrates only the signed integer
velocity byte. A high byte of 5 resets the velocity fraction. Direction 0 jumps
with -1344, directions 1/2 with -1104, directions 3/4 with -1280, and ladder/platform
jumps 5/6 with -912. Horizontal speed is 2 except the initial vertical jump.
A vertical jump permits one direction selection after a 48-pixel ascent.
Source scroll and player-screen coordinates are retained for camera-return and
landing decisions. Their sum supplies native world coordinates; the existing
Genesis viewport follows independently. Global source camera limits are unfinished.
Opposing up/down during a ladder jump cancels the request rather than reproducing
the source's infinite loop at 8899.

Oracle: `tools/run_player_motion_oracle.py` runs 309 cases / 24,620 updates, stopping
at 81EF before rendering. It compares all 25 native motion fields, including logical
scroll/screen coordinates, on floors, pits, walls, platforms, ceilings, ladders,
reversed controls, input changes, and preexisting falls. It does not execute attack,
hurt/death, rendering, external camera limits, or sound dispatch. Sound codes in
these routines are 1B jump, 1C landing, 1E ladder attach, 1F fall completion, 3B fall,
and periodic 1A climb. The cartridge currently emits its native jump cue only.

The cartridge resets this state on round/restart and externally changed positions,
exports ordinary Player velocity/grounded/climb/face, and supplies F426's low state
to reinforcement aiming. Other collision posture variants remain to be connected.
Attack and jump-attack now share the controller described below. Their source-specific
branch differences are preserved; only sound dispatch and the broader game-loop
scheduling/pool model remain separate.

## Graphics

Source 81EF uses root 9120 when armored and 9698 when unarmored, then pose byte
offset, selector*2, and (frame&7)*6. The ten gameplay poses and all six selectors
are compiled into 960 HeroFrame records. Source graphics attributes determine
four-piece body order and held-weapon flip/offset. The held weapon adds tier-1.
Native tests compare every linked-ROM record and 48 hardware sprite fixtures;
normal input verifies crouch, walk, jump, and reinforcement low-aim state.
Old renderer equivalence fixtures now keep the hero offscreen in both cartridges;
the changed player graphics are tested directly against source tables instead.
Weapon tier-five palette, invulnerability/armor-break graphics and death poses
remain presentation work. Attack poses now follow the source controller.

## Implemented attack and chain

Entry 8111 dispatches on F41B*2+F413: walk 8625, jump 8800, attack 8AEA,
jump+attack 8D0E. Three-bit history edges E904 set F41B and F421; holding fire
does not retrigger until released. F41A is attack active; F41D captures selector;
F41C is reach (4/5/5/6/6), F40D damage (1/2/4/8/16), from 9116+2*weaponTier.

8AEA starts attack when F41A==0, zeros horizontal velocity unless already jumping,
and zeros vertical velocity unless falling. It clears F447/F44B, selects attack
facing/posture (pure down derives a crouch selector from the prior facing), stores
F41D, sets chain bounds F44C=8/F44D=4 and active F41A=1. 8B79 retains F41D each
update. Initial windup pose is 2 standing / 8 jumping / 14 ladder. F447 counts
six windup updates. When F440 is active or the counter reaches 6, extended pose
is 4 standing / 10 jumping / 16 ladder and the chain starts extending.

Extension 8BE7: counter 0 places head at relative X +32 or -16. For counter >0,
convert the preceding head to code 1 chain link, set the next head 16 pixels farther
out, and increment F44B. Six 32-byte source slots F440/F460/.../F4E0. Head code
is 6F+weaponTier. At counter==reach set F44A=1, reset F447, then hold until 13.
8CA3 increments F447, calls the shared fall step if needed, and integrates. 8CB5
clears attack active/request, chain state and all six slots, returning pose to
0/6/12 according to standing/jumping/ladder. Chain remains extended through the
hold period; it is not a freely moving projectile.

83CC–8443 supplies chain sprite positions after body rendering. Relative X is
added to the player's screen-X low byte. Y is player Y+6 while jumping, on ladder,
or standing; otherwise Y+14 for crouch. Six slots stop at the first inactive one.
Body graphics flip determines chain flip; fifth weapon tier uses palette 6.

Jump+attack 8D0E reuses jump initialization but differs at important branches:
falling routes directly to attack; its upward side checks skip directions 5/6
without checking ladder state; it has no screen-Y<16 ceiling guard; vertical-jump
redirect checks raw input exactly 1/2 (no masking/reversal); descending at or below
origin clears E054 and sets F417 without forcing screenY=144. Gravity 8F21 then
routes to attack 8AEA. Collision/ladder/landing branches share 8A9A/8AAA/8A6C and
can bypass the attack update. These differences are preserved by the shared native jump helper.

Remaining integration work: per-pool global ordering and scanner cadence, full player
collision postures, hurt/death, source camera/main-loop limits and impact presentation. Existing reference/player_weapon.json witnesses
three dagger templates at A290, source attack tiers and constructor A0FD.

Dagger routine A0B9 has nine dedicated 32-byte slots, grouped into three volleys of
three. On F421, unless E915 or E02F gate it, find a group with all three inactive;
if none, clear request. Copy 96 bytes at A290. Facing from (F41D+1)&4 chooses saved
cursors A2EB/A2F6/A310 right or A32A/A335/A34F left (the loader advances by five
before loading). All start screen X=120; screen Y=playerY+8, or +16 when F426 low.
These source fixed-X placements assume source player X=112; native world placement
must account for the Genesis camera adaptation. Clear F421 and update all nine
immediately in A19F. Loader A1B8 is ordinary five-byte animation except it always
assigns both velocity bytes, with no 80 hold sentinel. After frame selection, fixed
080A applies previous-camera minus current-camera displacement, then integer X/Y
velocity. X retires when high byte is nonzero and low byte<240. Y uses the same
retirement test; high byte nonzero and low>=240 hides the sprite but retains actor.
A271 probes (8,8): empty/ladder skips the three-byte callback marker and resumes
at following jump; solid switches to explosion A392. Source collision explosions
also have root A36E (palette6), versus terrain explosion A392 (palette1).

Player death 8446 uses a separate nine-byte two-body frame format with count F43D,
cursor F43E and first advance +9. Each record is duration, body code/attr/dx/dy,
second-body code/attr/dx/dy. Motion is applied to sprite coordinates only, not player
world state, on frame transitions. A 00 record at 8524 clears held weapon/chain,
initializes second body at the first body's location, emits sounds1F/02, then chooses
root9C11 if F41E/F41F both zero, 9D3B if only F41F nonzero, otherwise 9E65 right or
9F8F left by selector. FF retires player and jumps fixed2013. Still audit the damage
entry that seeds this death sequence and the fixed2013 continuation.


## Integrated weapon verification and remaining differences

The combined controller oracle now covers 56,720 updates in 719 cases, including
five reaches, windup/extension/hold/release, early collision shortening, crouched
attacks, ladder/jump attacks, direction changes and repeated button presses. Native
`PlayerAttack` is 12 bytes: active/request/history/launch/selector/reach/damage,
counter/holding/hit/links/count. A rising edge after two released updates starts
an attack; holding does not repeat. Another press during an attack can request a
new dagger volley without restarting the current chain sequence.

`src/player_dagger.c` compiles eight roots and terrain continuation segments from
bank7 into native AnimClips. Three groups of three slots support three concurrent
volleys. 28,800 source slot updates in 32 cases verify both facings, low launch,
all trajectories, impacts, camera displacement, retirement and full-pool refusal.
Terrain impacts preserve source active80; weapon hits become active40 and use a
pending explosion transition. World positions replace the source screen position
plus camera correction. Native spawn X=playerWorldX+8 adapts source fixed screen
X120, which assumes its centered player X112. Poison retains the launch request;
a successful shop antidote cure clears it like fixed67CC.

`actor_chain_contact` matches 1,306 small/medium source boundary cases over twelve
constructor shapes. Every extended link has an 8/4 half box, inclusive edges and
source screen-byte behavior. Small/medium chain collision has no frame-parity gate;
daggers retain their even/odd pool gate. Large/wide weapon checks are gated on odd
frames. Chain impact sets holding/hit and counter10; later actors and subsequent
frames cannot receive chain/dagger hits until the attack clears. As in source30DC,
the actor receiving the chain hit still checks its daggers on that same update.
Medium categories16/29 and blocked large weak-point hits select the palette1 dagger
explosion; other hits select palette6. The weapon tier's current cached attack
strength supplies dagger half damage, rather than storing damage at dagger launch.

Cartridge checks compare 300 real-input controller updates directly with source
attack traces, inspect all five chain-head renderings and tier damage/reach values,
check three-shot volleys and no held-fire repeat, poison suppression, and crouched
chain damage with one-hit shortening. Chain and dagger graphics were inspected in
Genesis Plus GX. The production path no longer emits the provisional free-flying
chain or two generic daggers. Generic Shot slots remain for unported fallback
enemy shots and deliberately injected legacy regression fixtures.

Remaining combat/presentation gaps: global source actor/pool scan order, some
compound-boss contact/weak-point geometry, full low-posture player collision,
chain-hit spark and sounds, fifth-tier held-weapon palette/flip, source attack-state
cleanup across every rescue/death/status task, and natural full-game balance/routes.
The source death record format audited above remains to be implemented.

## Crouching contact integration

The cartridge exports `Game.player_low = F426 && !F412` after its player update.
Small/medium contacts shift the player origin down ten pixels and replace both
actor half extents with 3 while crouched (source3174/34D9); the player half sizes
remain 3/8. Thus the crouched box is not merely a shortened standing box. Jumping
always selects normal contact even when F426 remains set. Ordinary actors, lethal
zones, collectibles, shared projectile contacts, skeleton weapons, missile actors,
statue/hunter shells and explosions use this rule. Wave bosses and dragons now
receive that flag in their already-source-checked alternate large-contact helpers.

2,352 original-ROM comparisons cover twelve small/medium constructor shapes and
all low/jump combinations. Eighteen linked-cartridge one-contact-tick cases verify
real Down input changes collision and a live jump overrides the stored low bit.
Screen-coordinate wrapping outside the tested interior and remaining compound-boss
contact models still need completion.

## Death initialization and direction leads

Fixed2253 selects bank6 template B1CC and copies64 bytes to F400. Its tail initializes
F43D=1 and F43E=9C07, so the death loader's first +9 reaches a 00 marker at9C10;
8524 then chooses its animation root. Normal lethal damage fixed2F99 clears F41E,
HP and held/hit sprites, marks F400=40, and sets F41F=1 if player screen-X low byte
is less than the damaging actor's screen-X low byte, otherwise0. Source47F2 lethal
hazards set F41E=1 and clear chain sprites; hazard death chooses direction from the
player selector in8524. Time-expiry fixed2B83 sets normal death and derives F41F
from (selector+1)&4. Existing native `player_hurt` lacks a source actor position
argument, so accurate normal death direction will need passed contact context.
Fixed2013 after animation completion owns resource/persistence reset already
covered by the restart subsystem; its presentation/continue scheduling is still
separate. Source armor break is fixed7A09, also called by hazard/time death.

### Death implementation follow-through

The audited nine-byte source records are now compiled into typed native frame data
by tools/extract_player_death.py. src/player_death.c implements all four clips and
the terminal callback; actual damage paths pass source X. Twenty independent MAME
fixtures compare every sprite byte and duration over 6,580 updates. Runtime checks
exercise lethal missiles and hazards through the production life/restart path.
This supersedes the earlier pending-death notes, but does not establish source
hardware hiding at wrapped edges, armor-break fragments or complete continue UI.

### Armor-break implementation

Fixed 7A09 clears armor F3AD and attempts four common small-object allocations,
copying 32-byte templates at 7A6B/7A8B/7AAB/7ACB. Coordinates are player+8 on each
axis. Each clip has four stationary four-update frames, then four one-update
frames cycling signed velocities until the standard small-object edge retirement.
Native armor_break.c reuses animation_tick and small_actor_axis_active; clip data
is compiled by extract_armor_break.py. Original 2FE7 observations cover all four
profiles and five starting positions (3,600 updates). The source allocation pool
is not reproduced here; native effects reserve four slots. Original sound 17 and
palette/task side effects remain part of the broader audio/presentation work.
