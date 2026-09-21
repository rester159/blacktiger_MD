# BLACK TIGER: THE LAST HOUR — Roguelike Mode Implementation Spec

**Version:** 2.0 (Sega Genesis / Mega Drive target)
**Target:** Existing Black Tiger Genesis port
**Scope:** A complete, additive game mode. Does not modify Arcade mode.

---

## 0. CONSTRAINTS

### 0.1 Asset constraint (absolute)

**No new visual assets may be created.** Every visual must be one of:

1. An existing sprite/tile, used as-is
2. An existing sprite/tile rendered with a **different CRAM palette**
3. An existing sprite/tile with **different animation timing**
4. Existing **font tiles** composed into new text
5. **CRAM manipulation** (tints, cycling, desaturation, pulsing) or **VDP shadow/highlight mode**

Where this spec names a "new" weapon, armor, or enemy variant, it is always an existing sprite + palette + stat block. **Never draw anything.**

### 0.2 Genesis hardware budget (THE governing constraint)

This is a Mega Drive game. The following are hard ceilings, not guidelines. **Every system in this spec is designed around them.**

| Resource | Limit | Implication for this mode |
|---|---|---|
| **CRAM palettes** | **4 × 16 colors** (color 0 transparent) | Only ~60 colors on screen. Drives the entire affix redesign (§6). |
| Master palette | 512 colors, 3 bits/channel | All colors written as `$0BGR`, nibbles from `{0,2,4,6,8,A,C,E}` |
| Sprites | 80 total, **20 per scanline**, 320px of sprite per line | Hard cap on simultaneous enemies (§6.5) |
| Sprite sizes | 1×1 to 4×4 tiles (8×8 units) | — |
| VRAM | 64 KB = 2048 tiles, shared by tiles + sprites + font | Palette swaps cost **zero** VRAM. This is why the design works. |
| Work RAM | 64 KB | Generated stage must fit (§7.8) |
| Planes | A, B, + **Window** (non-scrolling) | Window plane = the HUD, free of sprite cost (§19) |
| Per-tile palette | 2-bit palette index per tilemap entry | Per-region palette zones are possible |
| CRAM DMA | ~128 bytes, cheap in vblank | Full palette swap every frame is affordable (§8.5) |
| CPU | 68000 @ 7.67 MHz | Generation must fit in the paused STAGE_INTRO window (§7.3) |
| Save | Battery SRAM, or password | No filesystem (§17) |

**The single most important consequence:** an affix is a CRAM change only. It costs **0 VRAM tiles and 0 DMA bandwidth**. This makes the affix system the most Genesis-appropriate content multiplier available — but it is bounded by the 4-palette ceiling, which is why only a subset is active per stage.

### 0.3 Determinism requirement (absolute)

The mode must be **deterministic given a seed**. Same seed + same inputs = same run. Required for co-op sync, daily seeds, and reproducible bugs. See §18.

### 0.4 Units

- **Tile** = 8×8 px (VDP native). **Block** = 16×16 px = 2×2 tiles, the level grid unit. All level distances in blocks.
- **Frame** = 1/60 s (NTSC). PAL: scale all timing constants by 6/5 at load.
- **Clock second** = one unit of the run clock (§2), not necessarily one real second.
- **TP** = Threat Points, the difficulty currency (§6.3).

---

## 1. MODE ENTRY AND RUN LIFECYCLE

### 1.1 Entry

Add `THE LAST HOUR` to the main menu below `ARCADE`. Selecting it opens **Run Setup**:

```
        BLACK TIGER: THE LAST HOUR

        RANK 7  -  THE IRON NAME
        XP  12,480 / 15,500

        SEED    [ K9XR2M ]   (RANDOM / ENTER / DAILY)
        WEAPON  < BLOOD FLAIL >
        ARMOR   < CHAIN >
        PACTS   < 0 >
        PLAYERS < 1 >

              PRESS START TO DESCEND
```

Seed alphabet: `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (32 chars, no ambiguous 0/O/1/I). 6 characters = 30 bits.

### 1.2 Lifecycle state machine

```
SETUP -> STAGE_INTRO -> STAGE_PLAY -> [STAGE_CLEAR | DEATH_RESPAWN | RUN_OVER]
STAGE_CLEAR -> GATE_ROOM -> STAGE_INTRO
STAGE_CLEAR (stage 16) -> RUN_VICTORY
DEATH_RESPAWN -> STAGE_PLAY
RUN_OVER / RUN_VICTORY -> RESULTS -> SETUP
```

- **STAGE_INTRO:** 150 frames. Shows stage number, biome, modifier, **and the 2 active affixes**. Clock paused. **Stage generation runs here** (§7.3).
- **GATE_ROOM:** Clock paused. Boon choice, guaranteed shop, run stats (§10.4).
- **RESULTS:** XP banked, rank-up shown. Always reached, even on death.

### 1.3 Run structure

16 stages, 4 acts of 4. `act_of(stage) = ((stage - 1) >> 2) + 1`

| Act | Stages | Elite Dragon | Act Boss |
|-----|--------|--------------|----------|
| I   | 1–4    | 2  | 4 |
| II  | 5–8    | 6  | 8 |
| III | 9–12   | 10 | 12 |
| IV  | 13–16  | 14 | **16 — BLACK TIGER** |

---

## 2. THE CLOCK (CORE SYSTEM)

The clock is the run's true health bar. **Build this first.**

### 2.1 Rules

- One clock persists across all 16 stages. It never resets.
- Counts down during `STAGE_PLAY` only. Paused in intro, gate, results, and during Hourglass.
- **Clock reaches 0 → run ends immediately.**
- Losing all vitality does **not** end the run. It costs clock time and respawns you.

### 2.2 Constants

Store as 16.16 fixed point, or as integer frames (recommended on 68000 — avoid division).

```
CLOCK_START        = 180.0 s   (10800 frames)
CLOCK_CAP          = 600.0 s   (36000 frames)
CLOCK_KILL_REWARD  = 3.0 s     flat, does NOT scale with TP
CLOCK_ELITE_REWARD = 8.0 s
CLOCK_STAGE_CLEAR  = 45.0 s
CLOCK_DRAGON_ELITE = 60.0 s
CLOCK_DRAGON_BOSS  = 90.0 s
CLOCK_DEATH_PENALTY= 60.0 s
CLOCK_LOW_WARNING  = 30.0 s
```

### 2.3 Drain rate

```
drain = base
      * ACT_DRAIN[act]
      * biome.drain_mult
      * modifier.drain_mult
      * product(active_curse.drain_mult)

ACT_DRAIN = { 1: 1.0, 2: 1.3, 3: 1.7, 4: 2.2 }
```

Implement as a per-frame decrement of a fixed-point accumulator. **No division in the main loop.** Precompute `frames_per_clock_tick` once per stage.

### 2.4 Design intent (do not tune away)

| Act | Expected net clock change per stage |
|-----|------------------------------------|
| I   | +35 to +50 |
| II  | +45 to +60 |
| III | +10 to +30 |
| IV  | −25 to +5  |

Players bank time early and bleed late. All constants live in one editable table (Appendix A).

### 2.5 Clock as currency

Wise Men, revives, and rerolls accept seconds. `SECONDS_PER_ZENNY = 1/833` (1 second ≈ 833 Zenny). Use a lookup table, not division.

---

## 3. PLAYER STATE

### 3.1 Stats (fits in ~32 bytes of work RAM per player)

```
vitality_current   u8      vitality_max      u8   (base 8, cap 16)
weapon_id          u8      weapon_tier       u8   (1..5)
throwable_id       u8      throwable_tier    u8   (1..5)
armor_id           u8      armor_tier        u8   (1..5)
zenny              u32
relics             u64 bitfield (45 bits used)
curses             u16 bitfield
hourglass_charges  u8      (max 3)
stage_kills        u16     run_kills         u16
```

### 3.2 Movement envelope (CANONICAL — the generator depends on this)

**Must match the shipped player controller exactly.** If the controller changes, these change with it, and the offline chunk-pair table (§7.2) must be regenerated.

```
MOVE_SPEED          = 1.6 blocks/sec
JUMP_PEAK_HEIGHT    = 3.5 blocks
JUMP_MAX_HORIZONTAL = 4.0 blocks
CLIMB_SPEED         = 1.2 blocks/sec
MAX_SAFE_FALL       = infinite
STAND_HEIGHT        = 2 blocks     CROUCH_HEIGHT = 1 block
```

**Rule R1 (load-bearing):** Level validation uses ONLY these base values. Any relic or armor improving mobility may open *optional branches* but must **never** be required on a critical path. Enforced offline (§7.2).

---

## 4. WEAPONS

All eight flails use the **existing flail sprite and its existing tier sprites**. Differentiation is palette + stat + timing only. **All eight share identical VRAM tiles.**

### 4.1 Base tier table

| Tier | Damage | Reach (blocks) | Swing cycle (frames) | Zenny |
|------|--------|----------------|----------------------|-------|
| 1 | 2  | 1.5 | 24 | — |
| 2 | 3  | 2.0 | 24 | 3,000  |
| 3 | 5  | 2.5 | 23 | 9,000  |
| 4 | 8  | 3.0 | 22 | 22,000 |
| 5 | 12 | 3.5 | 20 | 48,000 |

### 4.2 Flail variants

Multipliers apply to the §4.1 row for the current tier. Store as 8.8 fixed point; `speed_mult < 1.0` = faster.

| ID | Name | Palette entries | dmg× | speed× | reach× | Special |
|----|------|-----------------|------|--------|--------|---------|
| `IRON`    | Iron Flail    | grey (original) | 1.00 | 1.00 | 1.00 | — |
| `BLOOD`   | Blood Flail   | `$0006 $000A $000E` | 0.90 | 1.00 | 1.00 | Every 8th kill: +1 vitality |
| `FROST`   | Frost Flail   | `$0E84 $0EA6 $0EEC` | 0.85 | 1.10 | 1.00 | 15% on hit: freeze target 90 frames (reuse Hourglass freeze state) |
| `GOLD`    | Gold Flail    | `$0046 $008C $00EE` | 0.70 | 1.00 | 1.00 | +100% Zenny from kills |
| `BONE`    | Bone Flail    | `$08AA $0CCC $0EEE` | 0.75 | 1.00 | 1.00 | +2% dmg per stage kill, cap +100%, resets at gate |
| `VOID`    | Void Flail    | `$0402 $0806 $0C0A` cycling | 1.15 | 1.35 | 1.15 | Ignores `AZURE` armored immunity |
| `EMERALD` | Emerald Flail | `$0060 $00A0 $00E4` | 0.80 | 1.00 | 1.00 | Poison: 1 dmg/30 frames for 240 frames, refreshes, no stack |
| `STORM`   | Storm Flail   | `$0E40 $0EA0 $0EE8` cycling | 0.55 | 0.60 | 0.85 | — |

The flail uses **3 entries in the player palette** (§8.2). Only the equipped flail's 3 colors are loaded — the other seven cost nothing.

**Palette cycling:** `VOID` rotates its 3 entries every 8 frames. `STORM` every 3 frames. `FROST` every 20 frames. Purely cosmetic; 6 bytes of CRAM DMA in vblank.

### 4.3 Throwables

All use the **existing dagger sprite**. Infinite ammo, rate-limited. Shares 2 palette entries.

| Tier | Damage | Cooldown (frames) | Zenny |
|------|--------|-------------------|-------|
| 1 | 1 | 30 | — |
| 2 | 2 | 28 | 2,500 |
| 3 | 3 | 25 | 7,000 |
| 4 | 5 | 22 | 17,000 |
| 5 | 7 | 18 | 36,000 |

| ID | Name | Palette | Behavior |
|----|------|---------|----------|
| `DAGGER`   | Dagger        | steel (original) | Single projectile |
| `VOLLEY`   | Volley        | `$0468` bronze | 2 projectiles, ±12°, 60% damage each |
| `PIERCING` | Piercing Dart | `$0E82` blue | Passes through all enemies, cooldown ×1.4 |
| `GILDED`   | Gilded Dagger | `$00CE` gold | +50 Zenny per enemy hit, damage ×0.75 |

**Throwables always deal full damage to `AZURE` enemies.** This is the intended counterplay. Do not tune it away.

**Projectile sprite budget: 6 active maximum** (§6.5). Volley counts as 2.

---

## 5. ARMOR

The hero sprite already changes per armor tier. Sets are **palette variants of those existing tier sprites** — 4 entries in the player palette.

### 5.1 Tiers

| Tier | Damage absorbed/hit | Zenny |
|------|---------------------|-------|
| 1 | 0 | — |
| 2 | 1 | 3,000 |
| 3 | 2 | 9,000 |
| 4 | 3 | 22,000 |
| 5 | 4 | 48,000 |

### 5.2 Sets

| ID | Name | Palette direction | Effect |
|----|------|-------------------|--------|
| `LEATHER`  | Leather  | original brown | — |
| `CRIMSON`  | Crimson  | `$0004 $0008 $000C $000E` | +20% damage dealt, −1 absorption (min 0) |
| `ASHEN`    | Ashen    | `$0222 $0444 $0666 $0888` | Immune to fire and lava contact |
| `VERDANT`  | Verdant  | `$0040 $0080 $00C0 $00E2` | Immune to poison; +10% clock reward from kills |
| `OBSIDIAN` | Obsidian | `$0200 $0402 $0604 $0806` | Reflect 25% of contact damage |
| `GILDED`   | Gilded   | `$0026 $004A $008C $00EE` | +15% Zenny from all sources |

---

## 6. ENEMIES AND THE AFFIX SYSTEM

### 6.1 Base roster

Twelve existing enemy sprites. `XP = TP`. `Zenny = TP × 50`.

| ID | Sprite | Intro act | HP | Contact dmg | TP | Sprite cells |
|----|--------|-----------|----|-------------|----|--------------|
| `ZOMBIE`   | zombie         | I   | 1  | 1 | 1  | 1 |
| `BAT`      | bat            | I   | 1  | 1 | 1  | 1 |
| `SKELETON` | skeleton       | I   | 2  | 1 | 2  | 1 |
| `GREMLIN`  | gremlin/imp    | I   | 2  | 1 | 2  | 1 |
| `SERPENT`  | snake          | II  | 2  | 2 | 2  | 1 |
| `SCORPION` | scorpion       | II  | 3  | 2 | 3  | 1 |
| `GOLEM`    | rock monster   | II  | 5  | 2 | 5  | 2 |
| `EYE`      | floating eye   | III | 3  | 2 | 4  | 1 |
| `WRAITH`   | fire wraith    | III | 4  | 3 | 5  | 2 |
| `KNIGHT`   | armored knight | III | 6  | 3 | 6  | 2 |
| `HOUND`    | lava hound     | IV  | 8  | 3 | 8  | 2 |
| `DKNIGHT`  | dark knight    | IV  | 10 | 4 | 10 | 2 |

Map these IDs to whatever the port actually contains. If the roster differs, preserve the TP spread (1 → 10) and the intro-act pacing.

### 6.2 THE GENESIS AFFIX MODEL (read this before implementing anything visual)

On a 4-palette machine, seven simultaneous affix colors is impossible. The system is therefore split into two classes:

**Class A — Palette affixes.** Cost 3 CRAM entries each in the enemy palette. **Exactly 2 are active per stage**, rolled at generation and named in `STAGE_INTRO`.

**Class B — VDP mode affixes.** Cost **zero** palette entries, using shadow/highlight mode. **Always available in every stage.**

| Class | ID | Name | Visual | Effect | TP× |
|---|----|------|--------|--------|-----|
| — | `NONE`    | —        | original palette | — | 1.00 |
| **A** | `CRIMSON` | Enraged  | ramp `$0006 $000A $000E` | speed ×1.6, dmg ×1.5, HP ×0.6 | 1.4 |
| **A** | `AZURE`   | Armored  | ramp `$0E60 $0EA2 $0EC4` | **Immune to flail.** Full damage from throwables. | 1.8 |
| **A** | `VIOLET`  | Cursed   | ramp `$0806 $0C0A $0E0E` | On death spawns a static hazard (existing projectile sprite) 180 frames, 2 contact dmg | 1.5 |
| **A** | `BONE`    | Revenant | ramp `$0888 $0CCC $0EEE` | Revives once after 90 frames at 50% HP, as `NONE` | 1.7 |
| **A** | `EMERALDA`| Venomous | ramp `$0040 $0080 $00E0` | Contact applies poison: 1 dmg/30f for 240f | 1.3 |
| **B** | `VOIDB`   | Leech    | **VDP shadow** (half brightness) | Drains an extra 2.0 clock-sec/sec while on-screen | 2.0 |
| **B** | `GOLD`    | Gilded   | **VDP highlight** (brightened) | Zenny ×4, flees at speed ×1.4 | 1.2 |

**Why this split works:** shadow and highlight are thematically perfect for Leech (darkness) and Gilded (gleaming), and they are the two affixes a player most needs to identify instantly regardless of biome. Making them palette-free guarantees they are always readable everywhere.

**Implementation note on shadow/highlight:** enable VDP shadow/highlight mode globally for this game mode. A sprite rendered with its priority bit clear over a normal-priority background appears shadowed. Verify the exact operator semantics on real hardware or an accurate emulator (Genesis Plus GX / BlastEm) before committing — the interaction between sprite priority, plane priority, and palette-3 operator colors is subtle. If highlight proves unreliable in your renderer, fall back to giving `GOLD` a Class A slot and reducing per-stage Class A rolls to 1 + `VOIDB`.

### 6.3 Active affix rolling

```
function roll_stage_affixes(stage, biome, modifier, rng):
    pool = CLASS_A_AFFIXES          // 5 entries
    weights = biome.affix_weights   // §8.1 biases the roll
    if modifier forces an affix (e.g. BLOOD_MOON -> CRIMSON):
        active[0] = forced; pick active[1] from remaining
    else:
        active = weighted_pick_2_distinct(pool, weights, rng)
    return active   // exactly 2 Class A + VOIDB + GOLD always
```

Load the 6 CRAM entries for the 2 active ramps once, at stage load, via vblank DMA. **Zero per-frame cost thereafter.**

`STAGE_INTRO` must name them:

```
        STAGE 11
     VIOLET SANCTUM
      CURSED HOUR

   BEWARE:  ARMORED   CURSED
```

This is a design win, not a compromise: each stage has a legible tactical identity ("this is an Armored stage — bring daggers") instead of an unreadable seven-affix soup.

### 6.4 Effective values

```
tp    = base_tp * product(active_affix_tp_mults)
xp    = tp                                    (min 1)
zenny = base_tp * 50 * affix_zenny_mult
elite = (affix_count >= 1)                    -> CLOCK_ELITE_REWARD
```

**Stacking:** from Act III an enemy may carry 2 affixes, but **only from the stage's active set** (2 Class A + 2 Class B = at most 4 combinations of 2). Forbidden pairs: `AZURE`+`VOIDB`, `GOLD`+anything except `CRIMSON`, `BONE`+`BONE`.

### 6.5 Affix density by act

Fraction of spawned enemies receiving at least one affix:

| Act | Affix rate | Double-affix rate |
|-----|-----------|-------------------|
| I   | 0.05 | 0.00 |
| II  | 0.20 | 0.00 |
| III | 0.40 | 0.10 |
| IV  | 0.60 | 0.25 |

### 6.6 SPRITE BUDGET (hard VDP limit — violating this causes flicker/dropout)

```
MAX_ACTIVE_ENEMIES     = 10        (1P)   /  12 (2P)
MAX_ACTIVE_PROJECTILES = 6
MAX_ACTIVE_PICKUPS     = 8
MAX_ACTIVE_HAZARDS     = 4
PLAYER_CELLS           = 3 each (hero) + 3 (flail chain)
HUD                    = 0 sprites  (Window plane, §19)
```

Worst case 2P: 12 enemies × 2 cells (24) + 6 projectiles (6) + 8 pickups (8) + 4 hazards (4) + 12 player/flail = **54 of 80**. Headroom retained for boss sprites.

**Per-scanline rule (the real killer): no more than 8 enemy entities may occupy any 32-pixel horizontal band.** Enforce in the spawn manager, not the generator.

**Spawn/despawn manager:** spawn records live in RAM as a sorted-by-x list. An enemy activates when its anchor enters a 1.5-screen window and deactivates when it leaves by 2 screens. Deactivated enemies **do not despawn permanently** — they re-activate on re-entry with full HP, except enemies already killed (killed bitfield, 1 bit per spawn record). If `MAX_ACTIVE_ENEMIES` is reached, defer activation until a slot frees. **`VOIDB` enemies get activation priority** so their clock drain cannot be dodged by crowding.

---

## 7. LEVEL GENERATION

**Do not generate geometry procedurally.** Assemble hand-verified chunks. This is the highest-risk subsystem and the 68000 cannot afford a rejection loop — so validity is guaranteed **offline, by construction**.

### 7.1 Chunk library (offline, authored once)

Decompose the original rounds into **~120 chunks**, each a screen or half-screen slice. Chunks live in ROM.

```
Chunk record (ROM):
  id              u8
  width, height   u8, u8          // in blocks
  theme           u8              // cavern | ruins | inferno | keep
  act_mask        u8              // bitfield, which acts may use it
  flags           u8              // bit0 = branch_only
  traversal_cost  u8              // tenths of a second, for stage-length estimation
  socket_count    u8
  sockets[]       { edge:u2, pos:u6, class:u2 }   // edge L/R/U/D, class walk/jump/climb/drop
  anchor_count    u8
  anchors[]       { x:u6, y:u6, facing:u1, kind:u1, patrol:u4 }
  fixture_count   u8
  fixtures[]      { x:u6, y:u6, accepts:u4 }
  hazard_count    u8
  hazards[]       { x:u6, y:u6, type:u4 }
  tilemap_ptr     u32             // -> packed tilemap data
```

ROM cost: 120 chunks × ~224 block entries × 2 bytes ≈ **54 KB of tilemap** + ~6 KB metadata. Comfortable in a 1–2 MB cart.

### 7.2 OFFLINE PAIR-VALIDATION TABLE (replaces runtime rejection)

Build-time tool, run once per chunk-library change:

1. For every ordered chunk pair `(A, B)` and every compatible socket pairing, compose the two chunks.
2. Run the full reachability solver (§7.5) on the composition using **only** the §3.2 base envelope.
3. If A's entry can reach B's exit, set bit `(A, B)` in `PAIR_OK`.

`PAIR_OK` = 120 × 120 bits = **1.8 KB in ROM.**

**At runtime, assembly picks only from `PAIR_OK` neighbours, so every assembled spine is traversable by construction.** No rejection loop, no 200 attempts, no BFS on the 68000 in the hot path.

Also produced offline: `ENTRY_OK[chunk]` (spawn point is safe) and `SOCKET_INDEX` (for each chunk+edge+class, the list of chunks that connect).

**If the movement envelope in §3.2 ever changes, `PAIR_OK` MUST be regenerated.** Put this in the build script, not in a comment.

### 7.3 Runtime assembly (must complete inside STAGE_INTRO = 150 frames)

```
function generate_stage(stage, rng):
    act   = act_of(stage)
    biome = roll_biome(stage, rng)                  // §8.1
    mod   = roll_modifier(stage, rng)               // §9
    affix = roll_stage_affixes(stage, biome, mod, rng)  // §6.3

    spine = [ pick_entry_chunk(act, biome.theme, rng) ]
    for i in 1 .. SPINE_LENGTH[act] - 1:
        cands = SOCKET_INDEX[spine[i-1]] AND PAIR_OK[spine[i-1]]
                AND act_mask(act) AND theme_mask(biome.theme)
                AND NOT branch_only
        if cands empty: backtrack one step (max 8 backtracks)
        spine.push( rng.pick(cands) )

    branches = attach_branches(spine, BRANCH_COUNT[act], rng)   // same PAIR_OK test
    stage    = compose(spine, branches)

    place_keys_and_doors(stage, rng)      // §7.6, always succeeds by construction
    place_wise_men(stage, rng)            // §7.7
    populate_enemies(stage, ...)          // §7.8
    place_jars(stage, rng)
    return stage
```

```
SPINE_LENGTH = { 1:6, 2:7, 3:8, 4:10 }
BRANCH_COUNT = { 1:2, 2:3, 3:3, 4:4 }
MAX_BACKTRACK = 8
```

**Cost estimate:** ~10 table lookups + ~120 enemy placements + a tilemap blit. Well inside 150 frames on a 68000. If profiling shows otherwise, spread generation across the intro frames — it is already a paused state.

**`FALLBACK_STAGES`:** 16 hand-authored static stages in ROM. Used if backtracking exhausts, and used as the development baseline for milestones M1–M3 before the generator exists. **This table is required, not optional.**

### 7.4 Stage RAM budget

```
tilemap       10 chunks * 224 blocks * 2 bytes  = 4,480 B
spawn records 130 * 6 bytes                     =   780 B
killed bitfield                                 =    20 B
fixtures/doors/keys                             =   128 B
active entity slots  12 * 24 bytes              =   288 B
------------------------------------------------------------
                                                 ~5.7 KB of 64 KB
```

### 7.5 Reachability solver (offline tool only — never ships in the ROM)

BFS over a movement graph built from the §3.2 envelope.

```
node = (block_x, block_y, grounded)
edges:
  WALK  : adjacent ground blocks, both directions
  JUMP  : blocks inside the parabola from JUMP_PEAK_HEIGHT=3.5 /
          JUMP_MAX_HORIZONTAL=4.0, sampled at 0.25-block steps,
          rejecting any arc that clips solid geometry
  CLIMB : vertical movement on ladder/chain blocks
  DROP  : straight down until solid (MAX_SAFE_FALL infinite)
exclude any destination block flagged as a hazard
```

**Rule R1 enforcement:** this solver must read ONLY the §3.2 constants. It must never read relics, armor, or upgrades. Static assertion in the build tool.

### 7.6 Keys and doors

No locked doors in Act I. From Act II, place a door at a random spine index in `[2, len-1]`, and place the key in a fixture slot in a chunk topologically **before** the door. Because the spine is a linear chain, "before" is simply a lower index — always satisfiable, never fails.

### 7.7 Wise Men

- **2 to 3 per stage. At least one on the spine** — this guarantees the economy works for players who never explore.
- Never place one where reaching or breaking the stone requires unavoidable damage: reject any fixture with a hazard block adjacent or a spawn anchor within 3 blocks.

### 7.8 Enemy population

```
function populate_enemies(stage, stage_num, biome, mod, active_affixes, rng):
    budget  = TP_BUDGET(stage_num) * mod.tp_mult * (coop ? 1.0 : 1.0)
    target  = TARGET_COUNT(stage_num) * mod.count_mult * (coop ? 1.15 : 1.0)
    roster  = enemies_available_in_act(act_of(stage_num))
    anchors = filter_forbidden(shuffle(stage.anchors, rng), stage)

    spent = 0; placed = 0
    for anchor in anchors:
        if placed >= target * 1.2 or spent >= budget: break
        base = weighted_pick(roster, biome.roster_weights, rng)
        if not kind_compatible(base, anchor.kind): continue
        aff  = roll_affix(act, biome, mod, active_affixes, rng)   // ONLY from active set
        cost = base.tp * affix_tp_mult(aff)
        if spent + cost > budget * 1.1: continue
        emit_spawn_record(base, aff, anchor)
        spent += cost; placed += 1
```

**Forbidden spawn rules (all mandatory):**

- **F1.** No enemy within 2 blocks of any chunk entry socket.
- **F2.** No enemy on or within 1 block of the landing block of any critical-path jump.
- **F3.** No enemy within 3 blocks of a Wise Man fixture.
- **F4.** No more than 3 enemies in any 6×6 block window (Acts I–II); no more than 5 (Acts III–IV).
- **F5.** No `VOIDB` enemy in a branch. It must always be reachable and killable.
- **F6.** No more than 8 spawn anchors within any 32-pixel horizontal band (VDP scanline limit, §6.6).

### 7.9 Difficulty budget curves

```
TP_BUDGET(s)    = round(55 * 1.20^(s-1))     // ROM lookup table, no pow() on 68000
TARGET_COUNT(s) = round(40 + (s-1) * 5.33)   // ROM lookup table
```

| Stage | 1 | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 |
|-------|---|---|---|---|---|----|----|----|----|
| TP budget | 55 | 66 | 95 | 137 | 197 | 284 | 409 | 588 | 847 |
| Target count | 40 | 45 | 56 | 67 | 77 | 88 | 99 | 109 | 120 |
| Avg TP/enemy | 1.4 | 1.5 | 1.7 | 2.0 | 2.6 | 3.2 | 4.1 | 5.4 | 7.1 |

The rising avg TP/enemy automatically shifts composition from trash swarms to affixed elites. **Total run budget ≈ 4,808 TP.**

---

## 8. PALETTES AND BIOMES

### 8.1 THE PALETTE BUDGET (the most important table in this document)

Four palettes, sixteen entries each, entry 0 transparent.

| Pal | Owner | Allocation |
|-----|-------|------------|
| **0** | **Background** | 15 entries: biome tileset ramp. Rewritten at stage load. |
| **1** | **Background accent + HUD** | 8 entries: hazards (lava/water/poison), doors, jars. **6 entries: font + HUD.** **2 entries RESERVED for the clock — never touched by any effect.** |
| **2** | **Player + items** | 4 armor + 3 flail + 2 throwable + 4 pickups/Zenny + 2 shared |
| **3** | **Enemies** | 9 entries: base enemy ramps. **6 entries: the 2 active Class A affix ramps (3 each).** |

**Consequences that must be honoured everywhere:**

1. Only **2 Class A affixes per stage** (§6.2). This is a hardware fact, not a preference.
2. `VOIDB` and `GOLD` use VDP shadow/highlight and cost no entries.
3. **The clock's 2 entries in palette 1 are sacrosanct.** No tint, pulse, corruption, or biome load may write them. The clock is the game; it stays legible always.
4. Per-tile palette selection (2 bits per tilemap entry) means background blocks can pick palette 0 **or** 1 — use this for hazards and for per-region "corrupted zone" effects.

### 8.2 Biomes

A biome is a **palette-0 ramp + roster bias + stat modifiers**, rolled per stage, **decoupled from act**. The same tileset wears ten faces.

| ID | Name | Palette direction | Roster / affix bias | Modifiers |
|----|------|-------------------|---------------------|-----------|
| `STONE`   | Grey Stone     | cold slate (original) | uniform | — |
| `FROST`   | Frozen Hollow  | `$0E84`→`$0EEE` ice | `AZURE` ×2 | Hourglass ×1.5 duration |
| `GROTTO`  | Emerald Grotto | `$0020`→`$08E8` green | `EMERALDA` ×3 | Poison hazards live |
| `BONEC`   | Bone Cathedral | `$0468`→`$0EEE` ivory | `BONE` ×3, `SKELETON` ×2 | +1 Wise Man |
| `DROWNED` | Drowned Vault  | `$0600`→`$0EC8` teal | slow enemies ×2 | Zenny ×1.25 |
| `EMBER`   | Ember Deep     | `$0002`→`$008E` fire | `CRIMSON` ×2, `WRAITH`/`HOUND` ×2 | Lava hazards live |
| `RUST`    | Rust Works     | `$0024`→`$08CE` copper | `AZURE` ×3, `KNIGHT` ×2 | — |
| `SANCTUM` | Violet Sanctum | `$0402`→`$0E8E` magenta | `VIOLET` ×3 | Relic drops +1 |
| `GILDEDH` | Gilded Hall    | `$0024`→`$0AEE` gold | `GOLD` rate ×4 | Clock drain ×1.5 |
| `VOIDBI`  | The Void       | `$0000`→`$0888` mono | `VOIDB` ×3 | XP ×2, Zenny ×0.5 |

`VOIDBI` is Act III–IV only. All others may appear in any act, weighted toward hostility in late acts.

**False Biome (mandatory):** exactly once per run, in Act III, a stage loads the `STONE` palette but is populated with an Act IV roster and Act IV affix density. The palette lies to the player exactly once. Log it in results as `THE FALSE CALM`.

### 8.3 Channel assignment (prevents visual mud)

| Signal | Target | Frequency |
|--------|--------|-----------|
| Biome | Palette 0 ramp | Set once at stage load |
| Stage modifier | Palette 0 saturation + tint, layered | Set once at stage load |
| Curse corruption | Global desaturation of palettes 0 and 3 | Cumulative, permanent |
| Clock < 30s | Brightness pulse of palettes 0, 2, 3 | 1.2 Hz — **never palette 1** |
| Ambush | Palette 0 flash | 1 frame |
| Affix | **Palette 3 entries / VDP shadow-highlight only. Never background.** | Static |

### 8.4 Contrast guarantee

The 5 Class A ramps use color families that **no biome palette-0 ramp may use**. Build-time check: if a biome ramp contains a value within a Manhattan distance of 2 (in 3-bit RGB space) of any Class A affix ramp color, the build **fails**. This cannot be retrofitted — enforce it before authoring any biome palette.

Because only 2 affixes are active per stage, the biome roll may also **exclude** the 2 nearest-in-hue affixes, which makes the guarantee easy to satisfy in practice.

### 8.5 Palette effects (all CRAM DMA in vblank, ~128 bytes — cheap)

- **Lava flow** (`EMBER`): rotate 4 palette-1 entries, 6-frame interval
- **Water shimmer** (`DROWNED`): rotate 3 entries, 12-frame interval
- **Torch flicker**: 2-entry brightness swap, random 4–9 frame interval
- **Void breathing** (`VOIDBI`): palette-0 brightness sine, 0.15 Hz
- **Boss charge-up**: palette-0 saturation ramps +40% over the 45 frames before a dragon special — telegraphing with zero UI and zero sprites
- **Low-clock heartbeat**: palettes 0/2/3 brightness ±15%, 1.2 Hz, from `CLOCK_LOW_WARNING`
- **Hourglass freeze**: enable VDP shadow mode globally for the duration — one register write, instant, unmistakable

Implementation: maintain a **master palette table in work RAM** (64 words), apply effects to it, and DMA the whole thing to CRAM each vblank. Simpler and more robust than tracking dirty entries, and it fits the bandwidth easily.

### 8.6 Curse corruption

```
corruption = min(active_curse_count, 10) / 10
apply to palettes 0 and 3 only:
  desaturate toward luminance by (corruption * 0.85)
  shift hue toward red by (corruption * 12 degrees)
```

Palette 1 (HUD/clock) and the active affix ramps in palette 3 are **exempt** — build a per-entry exempt mask. At 8+ curses the world is near-monochrome blood while threats still burn in full color. **This is the mode's signature look.**

### 8.7 Safe-room palette

Gate Rooms and shop interiors load one **calm desaturated neutral** palette-0 ramp, identical in every biome. The player knows they are safe before parsing a single sprite.

---

## 9. STAGE MODIFIERS

One rolls per stage from **Act II onward** (never Act I). Layered on the biome per §8.3.

| ID | Name | Visual | Effect |
|----|------|--------|--------|
| `BLOOD_MOON`    | Blood Moon    | palette-0 red tint | Forces `CRIMSON` as an active affix; all enemies gain it; Zenny ×2 |
| `THE_DARK`      | The Dark      | palette-0 brightness −45% | Relic drops +3 |
| `CURSED_HOUR`   | Cursed Hour   | palette-0 green cycle | Clock drain ×2.0; XP ×2 |
| `GOLDEN_HOUR`   | Golden Hour   | palette-0 gold tint | All enemies gain `GOLD` (highlight, free); clock drain ×1.4 |
| `DEEP_FROST`    | Deep Frost    | palette-0 blue tint | All entities including the player move at ×0.7 |
| `DRAGONS_WRATH` | Dragon's Wrath| palette-0 edge pulse | A roaming dragon (existing sprite, 4 sprite cells) patrols; unkillable; contact 6 dmg |

Roll chance: Act II 40%, Act III 65%, Act IV 85%. Otherwise `NONE`.

`DRAGONS_WRATH` reduces `MAX_ACTIVE_ENEMIES` by 2 while active (sprite budget).

---

## 10. WISE MAN EVENTS

The petrified-old-man-in-stone framework already exists. Roll the event type on stone break.

### 10.1 Events

| ID | Name | Weight | Behavior |
|----|------|--------|----------|
| `SHOP`     | Shop        | 35 | 3 of N. One free reroll; further rerolls 1,500 Zenny, doubling within the stage. |
| `GAMBLE`   | Gamble      | 12 | 12,000 Zenny → random relic. 20% chance it is Cursed (§12.5). |
| `PACT`     | Pact        | 12 | Offers a named curse + payout (relic / 30,000 Zenny / +1 max vitality). Refusable free. |
| `CONTRACT` | Contract    | 10 | "Kill N before the gate." N = 40% of remaining stage spawns. Reward: 1 relic. |
| `BLESSING` | Blessing    | 12 | Free: full vitality **or** +40 clock seconds. Player picks. |
| `BROKER`   | Time Broker | 12 | Buys/sells clock seconds at `SECONDS_PER_ZENNY`, 15% spread. |
| `MIMIC`    | Mimic       | 7  | A `DKNIGHT` using the Wise Man's palette entries. Attacks on break. Drops 3× Zenny. |

`MIMIC` is disabled in Act I and **guaranteed at least once per run** from Act II.

### 10.2 Prices

| Purchase | Cost |
|----------|------|
| Weapon tier 2/3/4/5 | 3,000 / 9,000 / 22,000 / 48,000 |
| Armor tier 2/3/4/5 | 3,000 / 9,000 / 22,000 / 48,000 |
| Throwable tier 2/3/4/5 | 2,500 / 7,000 / 17,000 / 36,000 |
| Vitality vessel | 8,000, +6,000 per prior purchase |
| Hourglass charge | 4,000 |
| Relic | 15,000 |
| Shop reroll | 1,500, doubling within stage |
| Revive (co-op) | 25,000 **or** 45 clock seconds, doubling per use |

Total ladder ≈ 270,000 Zenny against ≈ 313,000 earned on a perfect clear. **Deliberately tight — the player must choose.**

### 10.3 Gate Room

Clock paused. Three elements:

1. **Boon: pick 1 of 3** from the unlocked pool: `+2 max vitality`, `+60 clock seconds`, `+15,000 Zenny`, `1 random relic`, `+1 weapon tier free`, `+2 Hourglass charges`.
2. **Guaranteed `SHOP`.**
3. Run stats: stage, clock, kills, Zenny, XP, relics, curses.

---

## 11. BOSSES

All from **existing dragon sprites**, differentiated by palette + attack-pattern recombination + stats. A boss temporarily takes over palette 3 (enemy palette); trash spawns are suppressed during boss fights, freeing both palette entries and sprite budget.

### 11.1 Elite dragons (stages 2, 6, 10, 14)

| Stage | Palette | HP | Pattern | Clock | XP | Zenny |
|-------|---------|----|---------|-------|----|-------|
| 2  | Green  | 40  | base, slow | +60 | 25  | 1,250 |
| 6  | Blue   | 110 | base + projectile volley | +60 | 50  | 2,500 |
| 10 | Ash    | 260 | base, ×1.4 speed | +60 | 100 | 5,000 |
| 14 | Shadow | 520 | base + teleport between 3 anchors | +60 | 175 | 8,750 |

### 11.2 Act bosses (stages 4, 8, 12)

| Stage | Name | Palette | HP | Phases | Clock | XP | Zenny |
|-------|------|---------|----|--------|-------|----|-------|
| 4  | Red Dragon  | red   | 80  | 1 | +90 | 75  | 3,750 |
| 8  | Blue Dragon | azure | 220 | 2 | +90 | 150 | 7,500 |
| 12 | Gold Dragon | gold  | 560 | 3 | +90 | 300 | 15,000 |

Each phase transition = palette-3 ramp swap (one vblank DMA) + switch to a different existing dragon's attack pattern + ×1.2 attack speed.

### 11.3 BLACK TIGER (stage 16)

HP 1,400. **Four phases**, each a palette swap on the same sprite, each adopting a different dragon's pattern.

| Phase | HP band | Sprite palette | Pattern | Arena (palette 0) |
|-------|---------|----------------|---------|-------------------|
| 1 | 100–75% | black  | Red Dragon | deep violet |
| 2 | 75–50%  | crimson| Blue Dragon volley | blood red |
| 3 | 50–25%  | gold   | Gold Dragon, ×1.3 speed | burning gold |
| 4 | 25–0%   | white  | all three interleaved, ×1.5 speed | full-palette pulse, 2 Hz |

Clock reward: **+300**. XP 600. Zenny 30,000. **Clock drain during this fight is ×3.0.** It is a race.

---

## 12. RELICS

45 relics. All effects are numeric or behavioral. Icons reuse existing jar / key / potion / gem sprites with palette-2 entries. Names and descriptions use existing font tiles.

Max 12 held (`u64` bitfield + a small count array for stacking). Duplicates stack unless marked `[unique]`.

### 12.1 Clock

| ID | Name | Effect |
|----|------|--------|
| `R01` | Sand in the Wound | Taking damage grants +5 clock seconds |
| `R02` | The Long Minute | Hourglass duration ×2 |
| `R03` | Deadline | While clock < 60s: +50% damage |
| `R04` | Usury | Wise Men accept only seconds, at half equivalent cost `[unique]` |
| `R05` | Hoarded Hour | `CLOCK_CAP` +200 |
| `R06` | Second Wind | `CLOCK_DEATH_PENALTY` → 30 `[unique]` |
| `R07` | Tempo | Each kill within 2s of the previous grants +1 extra second |
| `R08` | Frozen Ledger | Hourglass use refunds 5 clock seconds |
| `R09` | Overtime | `CLOCK_STAGE_CLEAR` +25 |
| `R10` | The Patient Blade | Standing still 3s: next hit ×3 damage |

### 12.2 Combat

| ID | Name | Effect |
|----|------|--------|
| `R11` | Executioner | Enemies at ≤20% max HP die instantly on any hit |
| `R12` | Chain Reaction | Killing a `VIOLET` enemy detonates its hazard immediately, 3-block radius, 6 dmg |
| `R13` | Bloodcount | Every 50th run kill: full vitality |
| `R14` | Heavy Head | +25% damage, −15% swing speed |
| `R15` | Whirl | Flail hits twice per swing at 50% damage |
| `R16` | Piercing Will | Flail ignores `AZURE` immunity `[unique]` |
| `R17` | Giant Slayer | +60% damage vs base HP ≥ 8 |
| `R18` | Swarmbane | +40% damage vs base HP ≤ 2 |
| `R19` | Airborne Fury | +100% damage while airborne |
| `R20` | Ricochet | Projectiles bounce once off walls |

### 12.3 Economy

| ID | Name | Effect |
|----|------|--------|
| `R21` | Midas Debt | All enemies gain `GOLD`; all enemies +40% HP `[unique]` |
| `R22` | Pauper's Blessing | While Zenny < 5,000: +30% damage |
| `R23` | Tithe | Spending 10,000 at a Gate Room grants +1 max vitality |
| `R24` | Grave Robber | +1 jar per chunk |
| `R25` | Merchant's Eye | Shops offer 4 items instead of 3 `[unique]` |
| `R26` | Free Hand | +1 free shop reroll per stage (stacks) |
| `R27` | Coin Magnet | Zenny auto-collects within 4 blocks |
| `R28` | Dragon's Hoard | Boss and elite dragon kills drop ×3 Zenny |

### 12.4 Defense

| ID | Name | Effect |
|----|------|--------|
| `R29` | Stoneskin | First hit taken in each chunk deals 0 damage |
| `R30` | Thorns | Reflect 30% of contact damage |
| `R31` | Second Skin | +2 max vitality |
| `R32` | Ward | Immune to poison |
| `R33` | Emberproof | Immune to fire and lava |
| `R34` | Ghost Step | +30 frames of invulnerability after taking damage |
| `R35` | Revenant's Pact | Once per run, survive a fatal hit at 1 vitality `[unique]` |

### 12.5 Cursed

Each counts toward curse corruption (§8.6).

| ID | Name | Effect |
|----|------|--------|
| `R36` | The Black Pact | +100% XP; clock drain ×1.5 |
| `R37` | Glass Barbarian | ×3 damage dealt; any hit taken zeroes vitality |
| `R38` | Sightless | Palette-0 brightness −50%; relic drops +2 |
| `R39` | Iron Coffin | +6 max vitality; −30% swing speed |
| `R40` | The Hungry Chain | +50% damage; −1 vitality every 10 seconds |
| `R41` | Gambler's Ruin | Shop prices ×0.5; shop contents fully random, no choice |
| `R42` | Mirror Curse | Enemies gain your relic damage bonuses |
| `R43` | Bound Hands | Throwables disabled; +75% flail damage |
| `R44` | The Long Fall | No branches generate (~30% shorter stages); clock drain ×0.7 |
| `R45` | Crown of Ash | Every biome becomes `EMBER`; Zenny +40% |

---

## 13. ECONOMY

```
xp    = base_xp * affix_mults * biome.xp_mult * modifier.xp_mult * pact_xp_mult
zenny = base_tp * 50 * affix_zenny_mult * biome.zenny_mult * modifier.zenny_mult
              * relic_zenny_mult
              * (armor  == GILDED ? 1.15 : 1.0)
              * (weapon == GOLD   ? 2.00 : 1.0)
```

Implement multipliers as 8.8 fixed point with a single accumulate pass. **No runtime division.**

### 13.1 Expected full-clear totals

| Source | Count | XP | Zenny |
|--------|-------|----|-------|
| Trash (4,808 TP) | ~1,245 | ~4,800 | ~240,000 |
| 4 Elite Dragons | 4 | 350 | 17,500 |
| 3 Act Bosses | 3 | 525 | 26,250 |
| Black Tiger | 1 | 600 | 30,000 |
| **Total** | **~1,253** | **~6,275** | **~313,750** |

Reference: die in Act I ≈ 350 XP. Act II ≈ 900. Act III ≈ 2,400. Act IV ≈ 4,300. Full clear ≈ 6,275.

**Zenny never persists between runs.** On death, all Zenny and gear are lost. XP is always banked in full.

---

## 14. META PROGRESSION

### 14.1 Ranks

| Rank | Name | Cumulative XP | Unlocks |
|------|------|---------------|---------|
| 1  | Wanderer        | 0      | Iron Flail, Leather, Dagger, boon: vitality |
| 2  | Stonebreaker    | 500    | Crimson armor, Volley, boon: clock |
| 3  | Chainbearer     | 1,400  | **Blood Flail**, shop reroll, relics R01–R10 |
| 4  | Gravewalker     | 2,800  | Ashen armor, **Gold Flail**, `GAMBLE` + `PACT` |
| 5  | Emberborn       | 4,800  | **Emerald Flail**, Piercing Dart, relics R11–R20 |
| 6  | The Iron Name   | 7,500  | Verdant armor, Hourglass purchasable, `BROKER` |
| 7  | Frostbound      | 11,000 | **Frost Flail**, Gilded Dagger, relics R21–R28, biomes FROST/GROTTO/BONEC |
| 8  | Dragonmarked    | 15,500 | Obsidian armor, `CONTRACT`, relics R29–R35 |
| 9  | Voidtouched     | 21,000 | **Void Flail**, Gilded armor, biomes DROWNED/RUST/SANCTUM |
| 10 | Stormcaller     | 28,000 | **Storm Flail**, **Bone Flail**, biomes GILDEDH/VOIDBI |
| 11 | The Cursed Name | 36,000 | Cursed relics R36–R45, all stage modifiers |
| 12 | BLACK TIGER     | 46,000 | **PACTS UNLOCKED** |

**~46,000 XP to max ≈ 25–30 runs of increasing depth.**

### 14.2 Pacts (Rank 12+)

Stack freely. Each grants **+15% XP multiplicatively**.

| ID | Name | Effect |
|----|------|--------|
| `P01` | The Short Hour | `CLOCK_START` −20% |
| `P02` | The Swarm | Affix rates ×1.5 |
| `P03` | The Toll | Wise Man prices ×2 |
| `P04` | No Mercy | No shop rerolls |
| `P05` | Brittle Bones | `vitality_max` −3 |
| `P06` | The Bleeding Hour | Clock drain ×1.25 |
| `P07` | Hard Iron | All enemies +30% HP |
| `P08` | The Blind Descent | Biome and active affixes hidden in `STAGE_INTRO` |
| `P09` | Dragon's Vigil | Extra elite dragons at stages 3, 7, 11, 15 |
| `P10` | The Last Hour | `CLOCK_CAP` = 240 |

---

## 15. TWO-PLAYER CO-OP

### 15.1 Scaling

```
ENEMY_HP_MULT    = 1.80
ENEMY_COUNT_MULT = 1.15
BOSS_HP_MULT     = 1.80
ZENNY_MULT       = 2.40
XP_MULT          = 1.00
```

**Zenny rationale — do not "simplify" this to 1.5×.** Two players need ~2× a solo budget to reach solo-equivalent gear. A 1.5× shared purse gives each player 0.75× while facing 1.8× HP enemies, making co-op ~2.4× harder than intended. 2.40× gives each 1.2× — a modest, correct co-op bonus.

### 15.2 Shared resources

- **Clock:** shared. One clock for the team.
- **Zenny:** shared purse; purchases are per-player, so splitting the purse is a real co-op decision.
- **XP:** shared pool; the full pool total is credited **to both profiles** — not split.
- **Relics:** per-player, except `[unique]` team relics (R04, R21, R25) which apply to both.

### 15.3 Palette cost of player 2

**This is the constraint that shapes the second character.** Palette 2 has 15 usable entries and is already fully allocated (§8.1).

Player 2 must therefore share the armor ramp with player 1, using a **4-entry recolor drawn from spare entries in palette 2**, or — preferred — **palette 2 is reorganised as 4 P1-armor + 4 P2-armor + 3 flail + 2 throwable + 2 shared pickups**, moving Zenny/jar pickups into palette 1's accent block.

Do this reorganisation **at M9, before writing any co-op rendering code.** Retrofitting a palette budget after the fact is the most expensive mistake available here.

### 15.4 Second character

- Palette-swap set of the existing hero sprites. **Identical hitbox, identical frame counts, identical stats.** Neither slot is the worse slot. Zero new VRAM tiles.
- **Both characters selectable by either player, including in 1-player mode.** Character choice belongs to the player, not the slot.

### 15.5 Camera

Shared camera, no split screen (not feasible on VDP here). If a player is off-screen for **180 continuous frames**, warp them to the other player. Never block scrolling. Black Tiger scrolls vertically; this matters.

### 15.6 Death and revival

- A downed player enters `DOWNED`: existing death animation frozen on its final frame, rendered with **VDP shadow** (free — no palette cost).
- Survivor may revive at a Wise Man: **25,000 Zenny or 45 clock seconds**, doubling per use that run.
- Downed players revive **free** at the next Gate Room.
- Both downed simultaneously: `−CLOCK_DEATH_PENALTY`, both respawn at the last chunk entry at full vitality.

### 15.7 Other

- Friendly fire **off**. Flails and projectiles pass through the partner.
- Drop-in / drop-out only at Gate Rooms. Scaling changes at the next stage boundary, never mid-stage.
- `MAX_ACTIVE_ENEMIES` rises to 12; **re-verify the per-scanline rule (§6.6) in 2P before shipping.**

---

## 16. HOURGLASS

The existing time-stop item, promoted to a build core.

- Max 3 charges. Start each run with 1.
- Freezes **all enemies and the clock** for 300 frames (×1.5 in `FROST`, ×2 with R02).
- Visual: enable **VDP shadow mode globally** for the duration. One register write. Free, instant, unmistakable.
- 4,000 Zenny (Rank 6+). Drops from jars at 4%.

---

## 17. SAVE DATA (SRAM)

No filesystem. Use battery-backed SRAM; provide a password fallback.

### 17.1 SRAM layout (64 bytes, plus checksum)

```
offset  size  field
0x00    4     magic 'BTLH'
0x04    1     version
0x05    6     player_name (font indices)
0x0B    4     xp_total (u32)
0x0F    1     rank
0x10    2     runs_started      0x12  2  runs_cleared
0x14    1     best_stage        0x15  2  best_clock_remaining (seconds)
0x17    4     total_kills
0x1B    2     unlocked_weapons + armors + throwables (bitfields)
0x1D    8     unlocked_relics (u64 bitfield)
0x25    2     unlocked_biomes   0x27  1  unlocked_events   0x28  2  unlocked_pacts
0x2A    4     daily_date (packed)  0x2E 1 daily_best_stage  0x2F 4 daily_best_score
0x33    8     seen_relics (u64)
0x3B    4     reserved
0x3F    1     checksum (XOR of 0x00..0x3E)
```

Two profile slots (P1, P2) fit in 128 bytes. Write on `RESULTS` only, never mid-run. **Bad checksum → start fresh, never crash.**

### 17.2 Password fallback

For hardware without a working battery: a 16-character password over the §1.1 alphabet encoding `xp_total` (20 bits) + rank (4) + unlock bitfields (40) + checksum (8) = 72 bits ≈ 15 chars. Shown on the `RESULTS` screen. Entry from the title screen.

---

## 18. RNG AND SEEDING

### 18.1 Requirements

One 32-bit seed per run from the 6-character code. **Separate, independently-advanced streams**, so changing one system cannot shift another — this is what keeps seeds stable across patches.

```
STREAM_LAYOUT   = mix(seed, 'LAYT')     STREAM_ENEMIES  = mix(seed, 'ENMY')
STREAM_BIOME    = mix(seed, 'BIOM')     STREAM_MODIFIER = mix(seed, 'MODR')
STREAM_AFFIX    = mix(seed, 'AFFX')     STREAM_WISEMAN  = mix(seed, 'WISE')
STREAM_RELIC    = mix(seed, 'RELC')     STREAM_DROPS    = mix(seed, 'DROP')
```

Per-stage: `mix(STREAM_X, stage_num)` — so stage 9 generates identically regardless of stages 1–8.

### 18.2 Algorithm

**xorshift32**, implemented explicitly in 68000 assembly or fixed C. Do **not** use any library RNG.

```
x ^= x << 13;  x ^= x >> 17;  x ^= x << 5;   // 32-bit
```

### 18.3 Daily seed

`daily_seed = mix('BTLH', packed_date)`, encoded to the 6-char alphabet. Same for everyone on that date. Leaderboard scoped per date in SRAM.

### 18.4 Score

```
score = stage_reached * 10000
      + run_kills * 25
      + floor(clock_remaining) * 100
      + (cleared ? 50000 : 0)
      + pact_count * 5000
```

---

## 19. HUD

**Render the HUD on the Window plane.** It does not scroll, costs **zero sprites**, and is unaffected by camera movement. This is the correct Genesis solution and it frees the entire sprite budget for gameplay.

```
 P1 [||||||||....]  ZENNY 42,150            0:47
 STAGE 11  VIOLET SANCTUM  -  CURSED HOUR
 ARMORED  CURSED      RELICS 7  CURSES 3  KILLS 604
```

- **The clock is the largest element on screen** and uses the 2 reserved palette-1 entries, exempt from every tint, pulse, and corruption stage.
- Below 30s the clock digits pulse at 1.2 Hz — implemented by alternating between the 2 reserved entries, **not** by touching the global palette.
- The stage's 2 active Class A affixes are named persistently in the HUD. The player should never have to guess what the colors mean this stage.

---

## 20. ACCEPTANCE TESTS

### 20.1 Determinism
- **T1.** Same seed + identical recorded inputs → identical final score across 100 runs of 16 stages. Zero divergence.
- **T2.** Stage 9 from seed X is byte-identical whether reached via stages 1–8 or generated directly.
- **T3.** Two players on the same seed generate identical stages for all 16 stages.

### 20.2 Generation
- **T4.** 10,000 seeds × 16 stages: every spine is composed only of `PAIR_OK` neighbours. Zero fallbacks used.
- **T5.** Offline: `PAIR_OK` is complete and correct for all 14,400 ordered pairs, verified by the solver.
- **T6.** No stage places a key behind its own door (10,000 seeds).
- **T7.** Every stage has ≥1 Wise Man on the critical path.
- **T8.** F1–F6 hold across 10,000 seeds.
- **T9.** Enemy count within ±20% of target, TP within ±15% of budget, 10,000 seeds.
- **T10.** `generate_stage` completes in < 150 frames on real hardware timing, worst case (act 4, max backtracks).
- **T11.** Offline solver never reads player upgrade state. Static assertion in the build tool.

### 20.3 Genesis hardware
- **T12.** **No frame exceeds 20 sprites on any scanline**, in 2P, with `DRAGONS_WRATH` active, on the densest generated stage across 1,000 seeds. Automated via emulator sprite-overflow flag.
- **T13.** Total active sprites never exceeds 80.
- **T14.** CRAM writes occur only during vblank. No mid-frame CRAM corruption.
- **T15.** Palette 1 entries reserved for the clock are bit-identical across every combination of biome × modifier × 10 curses × low-clock pulse × Hourglass.
- **T16.** Build fails if any biome palette-0 ramp collides (Manhattan distance < 2 in 3-bit RGB) with any Class A affix ramp.
- **T17.** Exactly 2 Class A affixes are loaded per stage; palette 3 is never over-allocated.
- **T18.** Work RAM for stage data stays under 8 KB.
- **T19.** **Zero new image assets.** Diff the art source directory against the base game; it must be unchanged.

### 20.4 Balance
- **T20.** Simulated average-skill run: net clock change per act falls inside the §2.4 bands.
- **T21.** A rank-1 player with starting gear clears stage 1 with ≥80% success across 200 seeds.
- **T22.** Full-clear XP total is 6,275 ±10%.
- **T23.** Full-clear Zenny is 313,750 ±10%, and is less than the total upgrade ladder cost.

### 20.5 Co-op
- **T24.** Both profiles receive the full XP total, not half.
- **T25.** Drop-out mid-stage does not change enemy scaling until the next stage boundary.
- **T26.** Off-screen warp triggers at 180 frames and never during a boss phase transition.

---

## 21. BUILD ORDER

Each milestone must be playable and verified before the next begins.

| M | Milestone | Contents | Done when |
|---|-----------|----------|-----------|
| **M0** | **Palette budget** | §8.1 allocation, reserved clock entries, §8.4 build-time contrast check, §15.3 P2 reorganisation decided **now** | Palette map is frozen and enforced in the build |
| **M1** | **The Clock** | §2 on the 16 hand-authored `FALLBACK_STAGES`. No generation, no affixes, no relics. | The clock hook is *fun* on static layouts. If not, stop and fix it here. |
| **M2** | **Affix system** | §6.2 two-class model, §6.6 sprite budget + spawn manager, shadow/highlight verified on real hardware | T12–T13, T17 pass; affixes readable on every biome |
| **M3** | **Biomes + modifiers** | §8.2, §8.5, §8.6, §9 | 16 static stages feel like 16 places across 3 runs; T15–T16 pass |
| **M4** | **Generation** | §7 in full, including the **offline `PAIR_OK` tool** | T4–T11 pass on 10,000 seeds |
| **M5** | **Economy + Wise Men** | §10, §13, §16 | T23 passes; shop decisions feel tight |
| **M6** | **Relics** | §12, all 45 | Three runs with the same weapon play differently |
| **M7** | **Bosses** | §11 | Black Tiger four-phase fight ships |
| **M8** | **Meta progression** | §14.1, §17 SRAM + password | T22 passes; ladder paces at 25–30 runs |
| **M9** | **Co-op** | §15, using the M0 palette reorganisation | T12 re-verified in 2P; T24–T26 pass |
| **M10**| **Pacts, daily seed, leaderboard** | §14.2, §18.3, §18.4 | Full T-suite green |

### The two rules that matter most

1. **Do M0 before anything else.** The palette budget and the P2 reorganisation cannot be retrofitted. Every visual decision in this document depends on them.
2. **Ship M1 and M2 and actually play them.** If the clock hook and the color language are not fun on the original static layouts, the level generator will not save the mode — and you will know that in days instead of months.

---

## APPENDIX A: TUNING TABLE

All of the following must be editable in one place.

```
clock:      start 180  cap 600  kill 3  elite 8  stage_clear 45
            dragon_elite 60  dragon_boss 90  death 60  low_warn 30
            act_drain [1.0, 1.3, 1.7, 2.2]   sec_per_zenny 1/833
difficulty: tp_base 55  tp_growth 1.20  count_base 40  count_step 5.33
            affix_rate [0.05, 0.20, 0.40, 0.60]
            double_affix [0.00, 0.00, 0.10, 0.25]
            class_a_per_stage 2                     // HARDWARE-BOUND, do not raise
generation: spine_len [6,7,8,10]  branch [2,3,3,4]  max_backtrack 8
player:     vit_base 8  vit_max 16  move 1.6  jump_peak 3.5
            jump_horiz 4.0  climb 1.2
sprites:    max_enemies 10 (12 in 2P)  max_proj 6  max_pickups 8  max_hazards 4
            max_per_32px_band 8                     // HARDWARE-BOUND
coop:       enemy_hp 1.80  enemy_count 1.15  boss_hp 1.80
            zenny 2.40  xp 1.00  warp_frames 180
meta:       rank_xp [0,500,1400,2800,4800,7500,11000,15500,21000,28000,36000,46000]
            pact_xp_mult 1.15
```

## APPENDIX B: WHAT NOT TO DO

- **Do not** assume more than 4 palettes. Every visual system in this spec is bounded by that.
- **Do not** raise `class_a_per_stage` above 2. It is a CRAM limit, not a design preference.
- **Do not** write CRAM outside vblank.
- **Do not** let any tint, pulse, or corruption effect touch the 2 reserved clock entries in palette 1.
- **Do not** let a biome ramp collide with a Class A affix ramp. Build-time failure.
- **Do not** run the reachability solver on the 68000. It is an offline tool; `PAIR_OK` is its shipped output.
- **Do not** let the solver see player upgrades. Rule R1 is load-bearing.
- **Do not** escalate difficulty by inflating HP. Use the TP budget and affix density.
- **Do not** exceed 20 sprites on a scanline. Enforce in the spawn manager, verify in the emulator.
- **Do not** tune co-op Zenny down to 1.5×. See §15.1.
- **Do not** retrofit the palette-2 split for player 2. Decide it at M0.
- **Do not** draw anything. Not one pixel. Palette, stats, timing, and text only.
