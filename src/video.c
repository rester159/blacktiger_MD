#include "ending.h"
#include "actor_dispatch.h"
#include "bonus.h"
#include "armor_break.h"
#include "player_motion.h"
#include "player_death.h"
#include "round_clear.h"
#include "game_over.h"
#include "player_dagger.h"
#include "assets.h"
#include "clear_screen_data.inc"
#include "ending_visual_data.inc"
#include "container.h"
#include "shop.h"
#include "progress.h"
#include "loot.h"
#include "sentry.h"
#include "emerge.h"
#include "wisp.h"
#include "zombie.h"
#include "boss.h"
#include "missile.h"
#include "statue_shell.h"
#include "npc.h"
#include "world.h"
#include <genesis.h>
#define BG_SLOTS 1056
#define SPR_BASE 1088
#define SPR_SLOTS 80
static u16 logical_to_slot[1700], slot_to_logical[BG_SLOTS], sprite_keys[SPR_SLOTS],
    sprite_stamp[SPR_SLOTS];
static u16 visible[1700];
/* A body occupies four existing 16x16 cache slots; both formats share the same VRAM. */
static u16 body_keys[SPR_SLOTS / 4], body_stamp[SPR_SLOTS / 4], body_eviction;
static u8 line_count[28], sprite_slot_for_key[16384];
static u16 eviction, sprite_eviction, sprite_count, sprite_uploads, epoch;
static s16 old_x, old_y;
static u8 clear_screen_active,ending_screen_active,ending_screen_scene,ending_screen_palette;
static u8 last_round = 255, last_mode = 255, last_opened, last_clear_phase;
static u8 last_bonus_entered,last_bonus_phases[4],last_game_over_phase,last_continue_digit;
u16 video_dma_bytes, video_dropped_sprites, video_cache_faults;
static u16 word_at(s16 x, s16 y) {
    const Round *r = &rounds[game.round];
    u16 w = r->width >> 3, h = r->height >> 3;
    if (x < 0 || y < 0 || x >= w || y >= h)
        return 0;
    {
        u16 word = r->map[((u16)y << (r->width == 2048 ? 8 : 7)) + x];
        return ((world_opened & world_rows[y]) || bonus_rows[y>>1]) ? world_word(x, y, word) : word;
    }
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
        b[i] = (y >= r->height / 8 || x + i >= w)
                   ? 0
                   : cached(((world_opened & world_rows[y]) || bonus_rows[y>>1]) ? world_word(x + i, y, p[i]) : p[i]);
    VDP_setTileMapDataRow(BG_B, b, y & 31, x & 63, 33, DMA_QUEUE_COPY);
    video_dma_bytes += 66;
}
static void column(s16 x, s16 y) {
    const Round *r = &rounds[game.round];
    u16 b[29], i, w = r->width >> 3, h = r->height >> 3;
    const u16 *p = r->map + ((u16)y << (r->width == 2048 ? 8 : 7)) + x;
    for (i = 0; i < 29; i++, p += w)
        b[i] = (x >= w || y + i >= h)
                   ? 0
                   : cached(((world_opened & world_rows[y + i]) || bonus_rows[(y+i)>>1]) ? world_word(x, y + i, *p) : *p);
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
        u16 v = (((world_opened & world_rows[y + i]) || bonus_rows[(y+i)>>1]) ? world_word(x, y + i, *p) : *p) & 2047;
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
        u16 v = (((world_opened & world_rows[y]) || bonus_rows[y>>1]) ? world_word(x + i, y, p[i]) : p[i]) & 2047;
        if (v >= 16)
            visible[v - 16] += delta;
    }
}
static void terrain_cell(u16 x,u16 y,u8 pass) {
 const Round *r=&rounds[game.round];u16 original,old,next,v;
 if(x<old_x || x>=old_x+33 || y<old_y || y>=old_y+29)return;
 original=r->map[(y<<(r->width==2048?8:7))+x];
 old=world_override(x,y,bonus_word_state(x,y,original,last_bonus_entered,last_bonus_phases),last_opened);
 next=world_word(x,y,original);
 if(old==next)return;
 if(!pass){
  v=old&2047;if(v>=16)visible[v-16]--;
  v=next&2047;if(v>=16)visible[v-16]++;
 }else{
  v=cached(next);
  VDP_setTileMapData(VDP_getBGBAddress(),&v,((y&31)<<6)|(x&63),1,2,DMA_QUEUE_COPY);
  video_dma_bytes+=2;
 }
}
static void terrain_state(void){
 u8 i;last_opened=world_opened;last_bonus_entered=bonus_entered;
 for(i=0;i<4;i++)last_bonus_phases[i]=bonus_phases[i];
}
static void terrain_updates(void) {
 const Round *r=&rounds[game.round];const BonusRound *b=&bonus_rounds[game.round];
 u16 i,j,dx,dy,shift=r->width==2048?7:6,width=r->width>>4;u8 changed=last_opened!=world_opened || last_bonus_entered!=bonus_entered,pass;
 if(!changed && !b->count)return;
 for(i=0;i<4;i++)changed|=last_bonus_phases[i]!=bonus_phases[i];
 if(!changed)return;
 /* Every affected cell is visited once; unpin all old patterns before allocation. */
 for(pass=0;pass<2;pass++){
  for(i=0;i<r->patch_count;i++){
   u16 cell=r->patches[i].cell,x=(cell&(width-1))*2,y=(cell>>shift)*2;
   if(x+2<=old_x || x>=old_x+33 || y+4<=old_y || y>=old_y+29)continue;
   if(!((last_opened^world_opened)&(1<<i)) && ((world_opened&(1<<i)) || (!bonus_rows[y>>1] && !bonus_rows[(y+2)>>1])))continue;
   for(dy=0;dy<4;dy++)for(dx=0;dx<2;dx++)terrain_cell(x+dx,y+dy,pass);
  }
  for(i=0;i<b->count;i++){
   u16 cell=b->patches[i].cell,x=(cell&(width-1))*2,y=(cell>>shift)*2;
   if(last_bonus_entered==bonus_entered && last_bonus_phases[b->patches[i].bank]==bonus_phases[b->patches[i].bank])continue;
   if(x+2<=old_x || x>=old_x+33 || y+2<=old_y || y>=old_y+29)continue;
   for(j=0;j<r->patch_count;j++)if(cell==r->patches[j].cell || cell==r->patches[j].cell+width)break;
   if(j<r->patch_count)continue;
   for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++)terrain_cell(x+dx,y+dy,pass);
  }
 }
 terrain_state();
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
            if (sprite_stamp[slot] != epoch && body_stamp[slot / 4] != epoch)
                break;
        }
        if (i == SPR_SLOTS) {
            video_dropped_sprites++;
            return;
        }
        body_keys[slot / 4] = 65535;
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
static void body_pieces(u16 code, u8 pal, s16 x, s16 y, u8 flip) {
    piece(code + (flip ? 1 : 0), pal, x, y, flip);
    piece(code + (flip ? 0 : 1), pal, x + 16, y, flip);
    piece(code + (flip ? 9 : 8), pal, x, y + 16, flip);
    piece(code + (flip ? 8 : 9), pal, x + 16, y + 16, flip);
}
static void body(u16 code, u8 pal, s16 x, s16 y, u8 flip) {
    u16 key = code + pal * 2048, block, i, j, start, end;
    if (code > 2038 || sprite_count >= 63 || x <= -32 || x >= 256 || y <= -32 || y >= 224)
        return;
    start = y < 0 ? 0 : y >> 3;
    end = (y + 39) >> 3;
    if (end > 28) end = 28;
    for (i = start; i < end; i++)
        if (line_count[i] > 14) {
            body_pieces(code, pal, x, y, flip);
            return;
        }
    for (block = 0; block < SPR_SLOTS / 4; block++)
        if (body_keys[block] == key) break;
    if (block == SPR_SLOTS / 4) {
        if (sprite_uploads > 28) {
            body_pieces(code, pal, x, y, flip);
            return;
        }
        for (i = 0; i < SPR_SLOTS / 4; i++) {
            block = body_eviction;
            if (++body_eviction == SPR_SLOTS / 4) body_eviction = 0;
            if (body_stamp[block] == epoch) continue;
            for (j = 0; j < 4; j++)
                if (sprite_stamp[block * 4 + j] == epoch) break;
            if (j == 4) break;
        }
        if (i == SPR_SLOTS / 4) {
            body_pieces(code, pal, x, y, flip);
            return;
        }
        for (j = 0; j < 4; j++) {
            u16 slot = block * 4 + j;
            if (sprite_keys[slot] != 65535) sprite_slot_for_key[sprite_keys[slot]] = 255;
            sprite_keys[slot] = 65535;
        }
        body_keys[block] = key;
        /* Hardware sprite tiles run down each column. Interleave top/bottom piece columns. */
        for (j = 0; j < 4; j++) {
            const u32 *source = object_patterns + (u32)(key + (j >> 1)) * 32 + (j & 1) * 16;
            u16 tile = SPR_BASE + block * 16 + j * 4;
            VDP_loadTileData(source, tile, 2, DMA_QUEUE);
            VDP_loadTileData(source + 8 * 32, tile + 2, 2, DMA_QUEUE);
        }
        sprite_uploads += 4;
        video_dma_bytes += 512;
    }
    body_stamp[block] = epoch;
    for (i = start; i < end; i++) line_count[i] += 2;
    VDP_setSpriteFull(sprite_count, x, y, SPRITE_SIZE(4, 4),
                      TILE_ATTR_FULL(pal ? PAL3 : PAL2, TRUE, FALSE, flip, SPR_BASE + block * 16),
                      sprite_count + 1);
    sprite_count++;
}
static void sprites(void) {
    Player *p = &game.p;
    u16 i;
    u8 pose=player_motion.pose/2;
    u8 f=player_motion.frame&7;
    const ClearFrame *clear=game.mode==CLEAR?round_clear_frame():0;
    const HeroFrame *h=&hero_frames[(clear && clear->hold?round_clear.original_armor:p->armor)!=0][pose][player_motion.selector*8+(f&7)];
    s16 x = PX(p->x) - game.cam_x, y = PX(p->y) - game.cam_y;
    sprite_count = sprite_uploads = 0;
    if(game.mode==GAMEOVER) {
        VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),0,0);
        VDP_updateSprites(1,DMA_QUEUE);return;
    }
    if (++epoch == 0) {
        epoch = 1;
        memset(sprite_stamp, 0, sizeof sprite_stamp);
        memset(body_stamp, 0, sizeof body_stamp);
    }
    memset(line_count, 0, sizeof line_count);
    if(game.mode==CLEAR && round_clear.phase==2) {
        /* The hero has departed before the Zenny award. */
    } else if(clear && !clear->hold) {
        for(i=0;i<6;i++)if(clear->visible&(1<<i)) {
            const ClearSprite *c=&clear->sprites[i];
            piece(c->code,c->palette,(u8)(round_clear.x+c->dx),(u8)(round_clear.y+c->dy),c->flip);
        }
    } else if(game.mode==DEAD && player_death_frame()) {
        const PlayerDeathFrame *d=player_death_frame();
        for(i=0;i<2;i++)body(d->code[i],d->palette[i],player_death.x[i],player_death.y[i],d->flip[i]);
    } else if (game.mode==CLEAR || !p->invincible || (game.frame & 4)) {
        body(h->code[0] - (h->flip ? 1 : 0), 0, x, y, h->flip);
        if(game.mode!=DEAD)piece(h->code[4]+p->weapon-1, 0, x + h->dx, y + h->dy, h->weapon_flip);
    }
    for(i=0;i<player_attack.count;i++) {
        u8 left=((player_attack.selector+1)&4)!=0;
        s16 cy=y+(player_motion.jumping || player_motion.ladder || !(player_motion.selector&3)?6:14);
        piece(i+1==player_attack.count?0x6f+p->weapon-1:1,p->weapon==5?6:0,
              x+(left?-16-16*i:32+16*i),cy,!left);
    }
    for(i=0;i<4;i++){
        const AnimFrame *f=armor_break_frame(i);ArmorFragment *a=&armor_fragments[i];
        s16 sy=a->y-game.cam_y;
        if(f && sy>=0 && sy<256)piece(f->code,f->palette,a->x-game.cam_x,sy,f->flip);
    }
    for(i=0;i<PLAYER_DAGGERS;i++) {
        const AnimFrame *f=player_dagger_frame(i);PlayerDagger *d=&player_daggers[i];
        if(f)piece(f->code,f->palette,d->x-game.cam_x,d->y-game.cam_y,f->flip);
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
        x = PX(a->x) - game.cam_x;
        y = PX(a->y) - game.cam_y;
        {
            const ActorDispatch *visual=&actor_dispatch[a->def];
            if(visual->frame){
                const AnimFrame *f=visual->frame(i);
                if(f){
                    if(visual->layout==DRAW_PIECE)piece(f->code,f->palette,x,y,f->flip);
                    else if(visual->layout==DRAW_BODY)body(f->code,f->palette,x,y,f->flip);
                    else{
                        u16 col,row,columns=visual->layout==DRAW_DRAGON?8:4;
                        for(row=0;row<4;row++)for(col=0;col<columns;col++)
                            piece(f->code+row*8+(f->flip?columns-1-col:col),f->palette,x+col*16,y+row*16,f->flip);
                    }
                }
                continue;
            }
        }
        code = d->code + (d->frames > 1 ? ((a->timer / 8) % d->frames) * 2 : 0);
        if (d->pieces == 4)
            body(code, d->palette, x, y, a->face > 0);
        else
            piece(code, d->palette, x, y, 0);
    }
    for (i = 0; i < MAX_ACTORS; i++) {
        s16 wx, wy;
        const AnimFrame *f = skeleton_weapon_frame(i, &wx, &wy);
        if (f)
            piece(f->code, f->palette, wx - game.cam_x, wy - game.cam_y, f->flip);
    }
    for(i=0;i<24;i++){const AnimFrame *f;if(!edge_shots[i].active)continue;f=edge_shot_frame(i);if(f)piece(f->code,f->palette,edge_shots[i].x-game.cam_x,edge_shots[i].y-game.cam_y,f->flip);}
    for(i=0;i<24;i++){const AnimFrame *f;if(!reinforcement_shots[i].active)continue;f=reinforcement_shot_frame(i);if(f)piece(f->code,f->palette,reinforcement_shots[i].x-game.cam_x,reinforcement_shots[i].y-game.cam_y,f->flip);}
    for(i=0;i<MAX_ACTORS;i++){const AnimFrame *f;if(!flailer_weapons[i].active)continue;f=flailer_weapon_frame(i);if(f)piece(f->code,f->palette,flailer_weapons[i].x-game.cam_x,flailer_weapons[i].y-game.cam_y,f->flip);}
    for(i=0;i<24;i++){const AnimFrame *f;if(!dragon_shots[i].active)continue;f=dragon_shot_frame(i);DragonShot *p=&dragon_shots[i];if(f){if(p->kind==2)body(f->code,f->palette,p->x-game.cam_x,p->y-game.cam_y,f->flip);else piece(f->code,f->palette,p->x-game.cam_x,p->y-game.cam_y,f->flip);}}
    for(i=0;i<MAX_WAVEBOSS_SEEDS;i++){const AnimFrame *f;if(!waveboss_seeds[i].active)continue;f=waveboss_seed_frame(i);if(f)piece(f->code,f->palette,waveboss_seeds[i].x-game.cam_x,waveboss_seeds[i].y-game.cam_y,f->flip);}
    for(i=0;i<MAX_CONTAINER_TRAPS;i++){const AnimFrame *f;if(!container_traps[i].active)continue;f=container_trap_frame(i);if(f)piece(f->code,f->palette,container_traps[i].x-game.cam_x,container_traps[i].y-game.cam_y,f->flip);}
    for(i=0;i<MAX_STATUE_SHELLS;i++) {
        const AnimFrame *f=hunter_shells[i].active?hunter_shell_frame(&hunter_shells[i]):0;
        if(f)piece(f->code,f->palette,hunter_shells[i].x-game.cam_x,hunter_shells[i].y-game.cam_y,f->flip);
        f=hunter_blasts[i].active?hunter_shell_frame(&hunter_blasts[i]):0;
        if(f)body(f->code,f->palette,hunter_blasts[i].x-game.cam_x,hunter_blasts[i].y-game.cam_y,f->flip);
        f=statue_shells[i].active?statue_shell_frame(&statue_shells[i]):0;
        if(f)piece(f->code,f->palette,statue_shells[i].x-game.cam_x,statue_shells[i].y-game.cam_y,f->flip);
        f=statue_blasts[i].active?statue_shell_frame(&statue_blasts[i]):0;
        if(f)body(f->code,f->palette,statue_blasts[i].x-game.cam_x,statue_blasts[i].y-game.cam_y,f->flip);
    }
    for(i=0;i<MAX_MISSILES;i++){const AnimFrame *f;if(!missiles[i].active)continue;f=missile_frame(i);if(f)piece(f->code,f->palette,missiles[i].x-game.cam_x,missiles[i].y-game.cam_y,f->flip);}
    for (i = 0; i < MAX_LOOT; i++) {
        const AnimFrame *f;
        if(!loot[i].active)continue;
        f=loot_frame(i);
        if (f)
            piece(f->code, f->palette, loot[i].x - game.cam_x, loot[i].y - game.cam_y, f->flip);
    }
    for (i = 0; i < rounds[game.round].patch_count; i++) {
        const AnimFrame *f = world_effect(i);
        if (f) {
            const Spawn *sp = &rounds[game.round].spawns[rounds[game.round].patches[i].source];
            body(f->code, f->palette, sp->x - 8 - game.cam_x, sp->y - 8 - game.cam_y, f->flip);
        }
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
static u8 last_shop = 255,last_keys=255,last_max_hp=255;
static void digits(char *p, u16 v, u16 count) {
    while (count) {
        p[--count] = '0' + v % 10;
        v /= 10;
    }
}
static void overlay(void) {
    u8 m = game.mode, changed = m != last_mode || (m==CLEAR && last_clear_phase!=round_clear.phase);
    if(m==GAMEOVER && (last_game_over_phase!=game_over.phase || last_continue_digit!=game_over.digit))changed=1;
    last_game_over_phase=game_over.phase;last_continue_digit=game_over.digit;
    last_clear_phase=round_clear.phase;
    char b[40];
    u16 stats = (game.p.hp << 12) | (game.p.armor << 8) | (game.p.weapon << 4) | game.p.lives;
    if (changed) {
        if(!clear_screen_active && !ending_screen_active)VDP_clearPlane(BG_A, TRUE);
        last_mode = m;
    }
    VDP_setTextPlane(WINDOW);
    if (stats != last_stats || last_keys!=container_keys || last_max_hp!=progress_max_hp) {
        strcpy(b, "HP 0/0 ARM0 W0 LIFE0");
        b[3] = '0' + game.p.hp;
        b[5] = '0' + progress_max_hp;last_max_hp=progress_max_hp;
        b[10] = '0' + game.p.armor;
        b[13] = '0' + game.p.weapon;
        b[19] = '0' + game.p.lives;
        text(1, 0, b);
        digits(b,container_keys,2);b[2]=0;text(27,0,b);text(24,0,"KEY");last_keys=container_keys;
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
        text(8, 18, "A ATTACK  B JUMP");
        text(6, 20, "UP: CLIMB / ENTER SHOP");
    } else if (m == RESCUE) {
        text(9, 5, "THANK YOU!");
    } else if (m == PAUSED)
        text(13, 12, "PAUSED");
    else if (m == SHOP) {
        u16 i;static const char *const names[]={"", "WEAPON 2", "WEAPON 3", "WEAPON 4", "WEAPON 5", "ARMOR 1", "ARMOR 2", "ARMOR 3", "ARMOR 4", "KEY", "ANTIDOTE", "EXIT"};
        text(5, 6, "THE OLD MAN'S SHOP");
        for(i=0;i<12;i++) {
            u8 item=shop_grid[i],x=2+(i/6)*16,y=9+(i%6)*2;
            if(!item)continue;
            text(x-1,y,game.shop_item==i?">":" ");text(x,y,names[item]);
            if(item!=11){u16 pad;digits(b,shop_price(item,shop_difficulty),5);b[5]=0;for(pad=0;pad<4 && b[pad]=='0';pad++)b[pad]=' ';text(x+9,y,b);}
        }
        text(3, 23, "A BUY   B / START EXIT");
    } else if (m == CLEAR) {
        /* The source bonus artwork is installed by video_frame. */
    } else if (m == DEAD)
        text(10, 11, "TRY AGAIN...");
    else if (m == GAMEOVER) {
        text(11, 10, "GAME OVER");
        if(game_over.phase==2) {
            text(10,12,"CONTINUE? 0");b[0]='0'+game_over.digit;b[1]=0;text(20,12,b);
            text(8,14,"START TO CONTINUE");
        }
    } else if (m == ENDING) {
        /* Source timed lettering is rendered by ending_screen. */
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
    clear_screen_active=ending_screen_active=0;
    terrain_state();
    u16 i;
    SYS_disableInts();
    VDP_setEnable(FALSE);
    DMA_flushQueue();
    memset(logical_to_slot, 255, sizeof logical_to_slot);
    memset(slot_to_logical, 255, sizeof slot_to_logical);
    memset(sprite_keys, 255, sizeof sprite_keys);
    memset(sprite_slot_for_key, 255, sizeof sprite_slot_for_key);
    memset(sprite_stamp, 0, sizeof sprite_stamp);
    memset(body_stamp, 0, sizeof body_stamp);
    memset(body_keys, 255, sizeof body_keys);
    eviction = sprite_eviction = body_eviction = epoch = 0;
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
static void bonus_screen(void) {
    /* This replaces the terrain cache only after the victory animation ends. */
    SYS_disableInts();
    VDP_setEnable(FALSE);
    DMA_flushQueue();
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    PAL_setColors(0, clear_screen_palette, 48, CPU);
    VDP_loadTileData(clear_screen_patterns, 16, CLEAR_SCREEN_TILES, DMA);
    VDP_setTileMapDataRect(BG_B, clear_bg[game.round], 0, 0, 32, 28, 32, DMA);
    VDP_setTileMapDataRect(BG_A, clear_fg[game.round], 0, 0, 32, 28, 32, DMA);
    VDP_setHorizontalScroll(BG_B,0);
    VDP_setVerticalScroll(BG_B,0);
    VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),0,0);
    VDP_updateSprites(1,DMA);
    {
        u16 value=game.coins, digits[5],i;
        for(i=5;i>0;i--){digits[i-1]=clear_digits[value%10];value/=10;}
        VDP_setTileMapDataRow(BG_A,digits,4,26,5,CPU);
    }
    clear_screen_active=game.round+1;
    VDP_setEnable(TRUE);
    SYS_enableInts();
}
static void ending_screen(void) {
    u16 y;
    if(!ending_screen_active) {
        SYS_disableInts();VDP_setEnable(FALSE);DMA_flushQueue();
        VDP_clearPlane(BG_A,TRUE);
        VDP_loadTileData(ending_font,1408,ENDING_FONT_TILES>32?32:ENDING_FONT_TILES,DMA);
#if ENDING_FONT_TILES > 32
        VDP_loadTileData(ending_font+32*8,1072,ENDING_FONT_TILES-32,DMA);
#endif
        PAL_setColors(48,ending_text_palette,4,CPU);
        ending_screen_active=1;ending_screen_scene=ending_screen_palette=255;
        VDP_setEnable(TRUE);SYS_enableInts();
    }
    if(ending_screen_scene!=ending.scene) {
        if(ending.scene) {
            SYS_disableInts();VDP_setEnable(FALSE);DMA_flushQueue();
            VDP_clearPlane(BG_B,TRUE);
            VDP_setHorizontalScroll(BG_B,0);VDP_setVerticalScroll(BG_B,0);
            VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),0,0);VDP_updateSprites(1,DMA);
            if(ending.scene==1) {
                VDP_loadTileData(ending_patterns,16,ENDING_TILES,DMA);
                VDP_setTileMapDataRect(BG_B,ending_map,0,0,32,28,32,DMA);
                PAL_setColors(0,ending_palette,32,CPU);
            }
            VDP_setEnable(TRUE);SYS_enableInts();
        }
        ending_screen_scene=ending.scene;
    }
    if(ending.scene==0 && ending.palette!=ending_screen_palette && ending.palette<10) {
        PAL_setColors(0,ending_fades+ending.palette*32,32,DMA_QUEUE);
        video_dma_bytes+=64;ending_screen_palette=ending.palette;
    }
    for(y=0;y<28;y++)if(ending_dirty_rows&(1UL<<y)) {
        u16 row[32],x;for(x=0;x<32;x++)row[x]=ending_glyphs[ending_text[y*32+x]];
        VDP_setTileMapDataRow(BG_A,row,y,0,32,DMA_QUEUE_COPY);video_dma_bytes+=64;
    }
    ending_dirty_rows=0;
}
volatile u16 video_cost[3];
void video_frame(void) {
    u32 t = getSubTick();
    video_dma_bytes = 0;
    if(game.mode==ENDING || (game.mode==GAMEOVER && ending.complete)) {
        ending_screen();overlay();
        video_cost[0]=getSubTick()-t;video_cost[1]=video_cost[2]=0;return;
    }
    if(ending_screen_active)video_round();
    if(game.mode==CLEAR && round_clear.phase==2 && game.round<7) {
        if(clear_screen_active!=game.round+1)bonus_screen();
        overlay();
        video_cost[0]=getSubTick()-t;video_cost[1]=video_cost[2]=0;
        return;
    }
    if(clear_screen_active)video_round();
    if (last_round != game.round || (game.cam_x >> 3) - old_x > 1 ||
        old_x - (game.cam_x >> 3) > 1 || (game.cam_y >> 3) - old_y > 1 ||
        old_y - (game.cam_y >> 3) > 1)
        video_round();
    terrain_updates();
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
