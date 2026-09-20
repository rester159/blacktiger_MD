#include "assets.h"
#include <genesis.h>
#define BG_SLOTS 1056
#define SPR_BASE 1088
#define SPR_SLOTS 80
static u16 logical_to_slot[1700], slot_to_logical[BG_SLOTS], sprite_keys[SPR_SLOTS],
    sprite_stamp[SPR_SLOTS];
static u16 visible[1700];
static u8 line_count[28], sprite_slot_for_key[16384];
static u16 eviction, sprite_eviction, sprite_count, sprite_uploads, epoch;
static s16 old_x, old_y;
static u8 last_round = 255, last_mode = 255;
u16 video_dma_bytes, video_dropped_sprites, video_cache_faults;
static u16 word_at(s16 x, s16 y) {
    const Round *r = &rounds[game.round];
    u16 w = r->width >> 3, h = r->height >> 3;
    if (x < 0 || y < 0 || x >= w || y >= h)
        return 0;
    return r->map[((u16)y << (r->width == 2048 ? 8 : 7)) + x];
}
static u16 cached(u16 word) {
    u16 logical = (word & 2047), slot, old;
    if (logical < 16)
        return 0;
    logical -= 16;
    if (logical >= 1700) {
        video_cache_faults++;
        return 0;
    }
    slot = logical_to_slot[logical];
    if (slot == 65535) {
        u16 n;
        for (n = 0; n < BG_SLOTS; n++) {
            slot = eviction;
            if (++eviction == BG_SLOTS)
                eviction = 0;
            old = slot_to_logical[slot];
            if (old == 65535 || !visible[old])
                break;
        }
        if (n == BG_SLOTS) {
            video_cache_faults++;
            return 0;
        }
        if (old != 65535)
            logical_to_slot[old] = 65535;
        logical_to_slot[logical] = slot;
        slot_to_logical[slot] = logical;
        VDP_loadTileData(rounds[game.round].patterns + (u32)logical * 8, 16 + slot, 1, DMA_QUEUE);
        video_dma_bytes += 32;
    }
    return (word & 0xf800) | (16 + slot);
}
static void row(s16 x, s16 y) {
    const Round *r = &rounds[game.round];
    u16 b[33], i, w = r->width >> 3;
    const u16 *p = r->map + ((u16)y << (r->width == 2048 ? 8 : 7)) + x;
    for (i = 0; i < 33; i++)
        b[i] = (y >= r->height / 8 || x + i >= w) ? 0 : cached(p[i]);
    VDP_setTileMapDataRow(BG_B, b, y & 31, x & 63, 33, DMA_QUEUE_COPY);
    video_dma_bytes += 66;
}
static void column(s16 x, s16 y) {
    const Round *r = &rounds[game.round];
    u16 b[29], i, w = r->width >> 3, h = r->height >> 3;
    const u16 *p = r->map + ((u16)y << (r->width == 2048 ? 8 : 7)) + x;
    for (i = 0; i < 29; i++, p += w)
        b[i] = (x >= w || y + i >= h) ? 0 : cached(*p);
    VDP_setTileMapDataColumn(BG_B, b, x & 63, y & 31, 29, 1, DMA_QUEUE_COPY);
    video_dma_bytes += 58;
}
static void pin(s16 x, s16 y, s16 delta) {
    u16 v = word_at(x, y) & 2047;
    if (v >= 16 && v < 1716)
        visible[v - 16] += delta;
}
static void pin_column(s16 x, s16 y, s16 delta) {
    const Round *r = &rounds[game.round];
    u16 w = r->width >> 3, h = r->height >> 3, i;
    const u16 *p = r->map + ((u16)y << (r->width == 2048 ? 8 : 7)) + x;
    if (x >= w)
        return;
    for (i = 0; i < 29 && y + i < h; i++, p += w) {
        u16 v = *p & 2047;
        if (v >= 16)
            visible[v - 16] += delta;
    }
}
static void pin_row(s16 x, s16 y, s16 delta) {
    const Round *r = &rounds[game.round];
    u16 w = r->width >> 3, i;
    const u16 *p = r->map + ((u16)y << (r->width == 2048 ? 8 : 7)) + x;
    if (y >= r->height / 8)
        return;
    for (i = 0; i < 33 && x + i < w; i++) {
        u16 v = p[i] & 2047;
        if (v >= 16)
            visible[v - 16] += delta;
    }
}
static void scene(u8 full) {
    s16 x = game.cam_x >> 3, y = game.cam_y >> 3, xx, yy;
    u16 i;
    if (!full && x == old_x && y == old_y)
        return;
    if (full || x - old_x > 1 || old_x - x > 1 || y - old_y > 1 || old_y - y > 1) {
        for (i = 0; i < 1700; i++)
            visible[i] = 0;
        for (yy = y; yy < y + 29; yy++)
            for (xx = x; xx < x + 33; xx++)
                pin(xx, yy, 1);
        for (yy = y; yy < y + 29; yy++) {
            row(x, yy);
            if (full && ((yy - y) & 3) == 3)
                DMA_flushQueue();
        }
    } else {
        if (x != old_x) {
            s16 remove = x > old_x ? old_x : old_x + 32, add = x > old_x ? x + 32 : x;
            pin_column(remove, old_y, -1);
            pin_column(add, old_y, 1);
        }
        if (y != old_y) {
            s16 remove = y > old_y ? old_y : old_y + 28, add = y > old_y ? y + 28 : y;
            pin_row(x, remove, -1);
            pin_row(x, add, 1);
        }
        if (x != old_x)
            column(x > old_x ? x + 32 : x, y);
        if (y != old_y)
            row(x, y > old_y ? y + 28 : y);
    }
    old_x = x;
    old_y = y;
}
static void piece(u16 code, u8 palette, s16 x, s16 y, u8 flip) {
    u16 key, slot, i;
    if (code >= 2048 || sprite_count >= 63 || x <= -16 || x >= 256 || y <= -16 || y >= 224)
        return;
    for (i = (y < 0 ? 0 : y >> 3); i < 28 && i < ((y + 23) >> 3); i++)
        if (line_count[i] >= 16) {
            video_dropped_sprites++;
            return;
        }
    key = code + palette * 2048;
    slot = sprite_slot_for_key[key];
    if (slot == 255) {
        if (sprite_uploads >= 32) {
            video_dropped_sprites++;
            return;
        }
        for (i = 0; i < SPR_SLOTS; i++) {
            slot = sprite_eviction;
            if (++sprite_eviction == SPR_SLOTS)
                sprite_eviction = 0;
            if (sprite_stamp[slot] != epoch)
                break;
        }
        if (i == SPR_SLOTS) {
            video_dropped_sprites++;
            return;
        }
        if (sprite_keys[slot] != 65535)
            sprite_slot_for_key[sprite_keys[slot]] = 255;
        sprite_keys[slot] = key;
        sprite_slot_for_key[key] = slot;
        VDP_loadTileData(object_patterns + (u32)key * 32, SPR_BASE + slot * 4, 4, DMA_QUEUE);
        sprite_uploads++;
        video_dma_bytes += 128;
    }
    sprite_stamp[slot] = epoch;
    for (i = (y < 0 ? 0 : y >> 3); i < 28 && i < ((y + 23) >> 3); i++)
        line_count[i]++;
    VDP_setSpriteFull(sprite_count, x, y, SPRITE_SIZE(2, 2),
                      TILE_ATTR_FULL(palette ? PAL3 : PAL2, TRUE, FALSE, flip, SPR_BASE + slot * 4),
                      sprite_count + 1);
    sprite_count++;
}
static void body(u16 code, u8 pal, s16 x, s16 y, u8 flip) {
    piece(code + (flip ? 1 : 0), pal, x, y, flip);
    piece(code + (flip ? 0 : 1), pal, x + 16, y, flip);
    piece(code + (flip ? 9 : 8), pal, x, y + 16, flip);
    piece(code + (flip ? 8 : 9), pal, x + 16, y + 16, flip);
}
static void sprites(void) {
    Player *p = &game.p;
    u16 i;
    u8 pose = p->climb ? 6 : p->attack ? 1 : !p->grounded ? 3 : 0;
    u8 f = p->climb    ? (game.frame / 8) & 3
           : p->attack ? (20 - p->attack) / 3
           : p->vx     ? (game.frame / 7) & 7
                       : 0;
    const HeroFrame *h = &hero_frames[pose][(p->face ? 0 : 8) + (f & 7)];
    s16 x = PX(p->x) - game.cam_x, y = PX(p->y) - game.cam_y;
    sprite_count = sprite_uploads = 0;
    if (++epoch == 0) {
        epoch = 1;
        memset(sprite_stamp, 0, sizeof sprite_stamp);
    }
    memset(line_count, 0, sizeof line_count);
    if (!p->invincible || (game.frame & 4)) {
        for (i = 0; i < 4; i++)
            piece(h->code[i], 0, x + (i & 1) * 16, y + (i >> 1) * 16, h->flip);
        piece(h->code[4], 0, x + h->dx, y + h->dy, h->weapon_flip);
    }
    for (i = 0; i < MAX_SHOTS; i++) {
        Shot *s = &game.shots[i];
        if (s->active)
            piece(s->enemy  ? 0x2a2
                  : s->kind ? 0x52
                            : 0x50,
                  s->enemy ? 5 : 0, PX(s->x) - game.cam_x - 8, PX(s->y) - game.cam_y - 8,
                  s->vx < 0);
    }
    for (i = 0; i < MAX_ACTORS; i++) {
        Actor *a = &game.actors[i];
        const ActorDef *d;
        u16 code;
        if (!a->active || (a->hit && (game.frame & 2)))
            continue;
        d = &actor_defs[a->def];
        code = d->code + (d->frames > 1 ? ((a->timer / 8) % d->frames) * 2 : 0);
        x = PX(a->x) - game.cam_x;
        y = PX(a->y) - game.cam_y;
        if (d->pieces == 4)
            body(code, d->palette, x, y, a->face > 0);
        else
            piece(code, d->palette, x, y, 0);
    }
    if (sprite_count)
        VDP_setSpriteLink(sprite_count - 1, 0);
    else {
        VDP_setSpriteFull(0, 0, -32, SPRITE_SIZE(1, 1), 0, 0);
        sprite_count = 1;
    }
    VDP_updateSprites(sprite_count, DMA_QUEUE);
    video_dma_bytes += sprite_count * 8;
}
static void text(u16 x, u16 y, const char *s) {
    VDP_drawText(s, x, y);
}
static u32 last_score = 0xffffffff;
static u16 last_coins = 65535, last_time = 65535, last_stats = 65535;
static u8 last_shop = 255;
static void digits(char *p, u16 v, u16 count) {
    while (count) {
        p[--count] = '0' + v % 10;
        v /= 10;
    }
}
static void overlay(void) {
    u8 m = game.mode, changed = m != last_mode;
    char b[40];
    u16 stats = (game.p.hp << 12) | (game.p.armor << 8) | (game.p.weapon << 4) | game.p.lives;
    if (changed) {
        VDP_clearPlane(BG_A, TRUE);
        last_mode = m;
    }
    VDP_setTextPlane(WINDOW);
    if (stats != last_stats) {
        strcpy(b, "HP 0 ARM 0 W0 LIFE 0");
        b[3] = '0' + game.p.hp;
        b[9] = '0' + game.p.armor;
        b[12] = '0' + game.p.weapon;
        b[19] = '0' + game.p.lives;
        text(1, 0, b);
        last_stats = stats;
    }
    if (game.score != last_score || game.coins != last_coins || game.time != last_time) {
        strcpy(b, "000000 Z0000 T000 R0");
        digits(b, (u16)(game.score / 1000), 3);
        digits(b + 3, (u16)(game.score % 1000), 3);
        digits(b + 8, game.coins, 4);
        digits(b + 14, game.time, 3);
        b[19] = '1' + game.round;
        text(1, 1, b);
        last_score = game.score;
        last_coins = game.coins;
        last_time = game.time;
    }
    VDP_setTextPlane(BG_A);
    if (!changed && !(m == SHOP && last_shop != game.shop_item))
        return;
    last_shop = game.shop_item;
    if (m == TITLE) {
        text(9, 7, "BLACK TIGER");
        text(7, 10, "SGDK DEVELOPMENT BUILD");
        text(10, 14, "PRESS START");
        text(4, 18, "A ATTACK  B JUMP  C MAGIC");
        text(6, 20, "UP: CLIMB / ENTER SHOP");
    } else if (m == PAUSED)
        text(13, 12, "PAUSED");
    else if (m == SHOP) {
        text(8, 6, "THE OLD MAN'S SHOP");
        text(7, 9, "WEAPON         100");
        text(7, 11, "ARMOR          150");
        text(7, 13, "VITALITY        75");
        text(7, 15, "MAGIC           50");
        text(5, 9, " ");
        text(5, 11, " ");
        text(5, 13, " ");
        text(5, 15, " ");
        text(5, 9 + game.shop_item * 2, ">");
        text(5, 19, "A BUY    B / START EXIT");
    } else if (m == CLEAR) {
        text(10, 11, "ROUND CLEAR");
    } else if (m == DEAD)
        text(10, 11, "TRY AGAIN...");
    else if (m == GAMEOVER) {
        text(11, 10, "GAME OVER");
        text(8, 14, "START TO CONTINUE");
    } else if (m == ENDING) {
        text(6, 9, "THE DARKNESS IS BROKEN");
        text(8, 12, "THANK YOU FOR PLAYING");
        text(9, 16, "PRESS START");
    }
}
void video_init(void) {
    VDP_setScreenWidth256();
    VDP_setPlaneSize(64, 32, TRUE);
    VDP_setBGAAddress(0xc000);
    VDP_setBGBAddress(0xe000);
    VDP_setWindowAddress(0xd000);
    VDP_setHScrollTableAddress(0xf000);
    VDP_setSpriteListAddress(0xf400);
    VDP_setWindowVPos(FALSE, 2);
    VDP_setTextPalette(PAL3);
    VDP_setTextPriority(TRUE);
    DMA_setMaxQueueSize(192);
    DMA_setBufferSize(8192);
    DMA_setMaxTransferSize(7200);
    VDP_setBackgroundColor(0);
}
void video_round(void) {
    u16 i;
    SYS_disableInts();
    VDP_setEnable(FALSE);
    DMA_flushQueue();
    memset(logical_to_slot, 255, sizeof logical_to_slot);
    memset(slot_to_logical, 255, sizeof slot_to_logical);
    memset(sprite_keys, 255, sizeof sprite_keys);
    memset(sprite_slot_for_key, 255, sizeof sprite_slot_for_key);
    memset(sprite_stamp, 0, sizeof sprite_stamp);
    eviction = sprite_eviction = epoch = 0;
    PAL_setColors(0, rounds[game.round].palette, 32, CPU);
    PAL_setColors(32, object_palette, 32, CPU); /* SGDK font uses foreground pen 15. */
    PAL_setColor(63, 0xeee);
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    VDP_clearPlane(WINDOW, TRUE);
    for (i = 0; i < 2; i++)
        VDP_fillTileMapRect(WINDOW, TILE_ATTR_FULL(PAL2, TRUE, FALSE, FALSE, 0), 0, i, 32, 1);
    scene(1);
    DMA_flushQueue();
    last_round = game.round;
    last_mode = 255;
    last_stats = last_coins = last_time = 65535;
    last_score = 0xffffffff;
    VDP_setEnable(TRUE);
    SYS_enableInts();
}
volatile u16 video_cost[3];
void video_frame(void) {
    u32 t = getSubTick();
    video_dma_bytes = 0;
    if (last_round != game.round || (game.cam_x >> 3) - old_x > 1 ||
        old_x - (game.cam_x >> 3) > 1 || (game.cam_y >> 3) - old_y > 1 ||
        old_y - (game.cam_y >> 3) > 1)
        video_round();
    scene(0);
    video_cost[0] = getSubTick() - t;
    t = getSubTick();
    VDP_setHorizontalScroll(BG_B, -game.cam_x);
    VDP_setVerticalScroll(BG_B, game.cam_y);
    sprites();
    video_cost[1] = getSubTick() - t;
    t = getSubTick();
    overlay();
    video_cost[2] = getSubTick() - t;
}
