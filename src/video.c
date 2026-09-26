#include "ending.h"
#include "frontend.h"
#include "intro.h"
#include "boss_rush.h"
#include "arena_video.h"
#include "backdrop.h"
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
#include "npc_sequence_visual.inc"
#include "container.h"
#include "shop.h"
#include "progress.h"
#include "loot.h"
#include "pots.h"
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
#include "sprite_atlas_index.inc"
#define BG_SLOTS 996
#define MAX_SCROLL_STRIPS 4
#define SPR_BASE 1088
#define SPR_SLOTS 80
static u16 logical_to_slot[1800], slot_to_logical[BG_SLOTS], sprite_keys[SPR_SLOTS],
    sprite_stamp[SPR_SLOTS];
static u16 visible[1800];
/* Logical words already resolved for the ring-buffer viewport. Reuse them
   when unpinning and submitting rows instead of re-querying dynamic terrain. */
static u16 visible_words[2048];
/* A body occupies four existing 16x16 cache slots; both formats share the same VRAM. */
static u16 body_keys[SPR_SLOTS / 4], body_stamp[SPR_SLOTS / 4], body_eviction;
static u8 line_count[28], sprite_slot_for_key[16384];
static u16 eviction, sprite_eviction, sprite_count, sprite_uploads, epoch;
static s16 old_x, old_y;
static u8 terrain_wrapped;
static const u16 *terrain_map;
static const u32 *terrain_patterns;
static u16 terrain_slots, terrain_width, terrain_height, terrain_shift;
static const Backdrop *terrain_backdrop;
static u8 shop_screen_active,torch_phase[4];
static u8 clear_screen_active,ending_screen_active,ending_screen_scene,ending_screen_palette;
static u8 poison_palette_active;
static u8 last_round = 255, last_mode = 255, last_opened, last_clear_phase;
static u8 last_bonus_entered,last_bonus_phases[4],last_game_over_phase,last_continue_digit;
u16 video_dma_bytes, video_dropped_sprites, video_cache_faults;
volatile u16 video_reload_count;
static u16 backdrop_word(u16 word){
 if(terrain_backdrop)return (word&0xf800)|0x8000|(word&0x2000?terrain_backdrop->remap1:terrain_backdrop->remap0)[word&2047];
 return word;
}
__attribute__((noinline)) static u16 dynamic_word(u16 x,u16 y,u16 word){return world_word(x,y,word);}
/* Cache slots are usually allocated consecutively. Batch their 32-byte
   patterns into one DMA request instead of setting up a transfer per tile. */
static u32 *terrain_upload;
static u16 terrain_upload_start,terrain_upload_count;
static void terrain_upload_flush(void){
 if(terrain_upload_count){
  VDP_loadTileData(terrain_upload,16+terrain_upload_start,terrain_upload_count,DMA_QUEUE_COPY);
  terrain_upload_count=0;
 }
}
static void terrain_upload_tile(u16 slot,const u32 *s){
 u32 *d;
 if(terrain_upload_count && (slot!=terrain_upload_start+terrain_upload_count || terrain_upload_count==32))terrain_upload_flush();
 if(!terrain_upload_count)terrain_upload_start=slot;
 d=terrain_upload+(terrain_upload_count++*8);
 d[0]=s[0];d[1]=s[1];d[2]=s[2];d[3]=s[3];
 d[4]=s[4];d[5]=s[5];d[6]=s[6];d[7]=s[7];
}
static u16 cached(u16 word) {
    u16 logical = (word & 2047), slot, old;
    const u16 slots=terrain_slots;
    if (logical < 16)
        return 0;
    logical -= 16;
    if (logical >= 1800) {
        video_cache_faults++;
        return 0;
    }
    slot = logical_to_slot[logical];
    if (slot == 65535) {
        u16 n;
        for (n = 0; n < slots; n++) {
            slot = eviction;
            if (++eviction == slots)
                eviction = 0;
            old = slot_to_logical[slot];
            if (old == 65535 || !visible[old])
                break;
        }
        if (n == slots) {
            video_cache_faults++;
            return 0;
        }
        if (old != 65535)
            logical_to_slot[old] = 65535;
        logical_to_slot[logical] = slot;
        slot_to_logical[slot] = logical;
        terrain_upload_tile(slot,terrain_backdrop && logical>=terrain_backdrop->original_tiles?terrain_backdrop->extra+(u32)(logical-terrain_backdrop->original_tiles)*8:terrain_patterns + (u32)(game.round==7 && !boss_rush.active && bonus_phases[logical&3]?torch_alternate[logical]:logical) * 8);
        video_dma_bytes += 32;
    }
    return (word & 0xf800) | (16 + slot);
}
static void row(s16 x,s16 y) {
 u16 b[33],i,at=(y&31)<<6;
 for(i=0;i<33;i++)b[i]=cached(visible_words[at|((x+i)&63)]);
 VDP_setTileMapDataRow(BG_B,b,y&31,x&63,33,DMA_QUEUE_COPY);video_dma_bytes+=66;
}
static void column(s16 x,s16 y) {
 u16 b[29],i;
 for(i=0;i<29;i++)b[i]=cached(visible_words[(((y+i)&31)<<6)|(x&63)]);
 VDP_setTileMapDataColumn(BG_B,b,x&63,y&31,29,1,DMA_QUEUE_COPY);video_dma_bytes+=58;
}
/* Strip walkers keep the map and ring positions in registers. Dynamic world
   patches retain the scalar resolver; ordinary tiles need no per-cell call. */
static void pin_column(s16 x,s16 y,s16 delta) {
 u16 i,at=((y&31)<<6)|(x&63),mx=(u16)x&(terrain_width-1);
 for(i=0;i<29;i++,y++,at=(at+64)&2047) {
  u16 word,v,my=WORLD_WRAP_Y?((u16)y&(terrain_height-1)):(u16)y;
  if(delta>0){
   word=my<terrain_height?terrain_map[(u16)((my<<terrain_shift)+mx)]:0;
   if(my<terrain_height){
    if((world_opened & world_rows[my]) || bonus_rows[my>>1])word=dynamic_word(mx,my,word);
    word=backdrop_word(word);
   }
   visible_words[at]=word;
  }else word=visible_words[at];
  v=word&2047;if(v>=16 && v<1816)visible[v-16]+=delta;
 }
}
static void pin_row(s16 x,s16 y,s16 delta) {
 u16 i,base=(y&31)<<6,rx=x&63,mx=(u16)x&(terrain_width-1);
 u16 my=WORLD_WRAP_Y?((u16)y&(terrain_height-1)):(u16)y;
 u8 valid=my<terrain_height;
 const u16 *map=valid?terrain_map+(u16)(my<<terrain_shift):terrain_map;
 u8 dynamic=valid && ((world_opened & world_rows[my]) || bonus_rows[my>>1]);
 for(i=0;i<33;i++,rx=(rx+1)&63,mx=(mx+1)&(terrain_width-1)) {
  u16 word,v;
  if(delta>0){
   word=valid?map[mx]:0;
   if(valid){if(dynamic)word=dynamic_word(mx,my,word);word=backdrop_word(word);}
   visible_words[base+rx]=word;
  }else word=visible_words[base+rx];
  v=word&2047;if(v>=16 && v<1816)visible[v-16]+=delta;
 }
}
static s16 terrain_view_x(s16 x){if(!terrain_wrapped)return x;return old_x+(((u16)(x-old_x))&(terrain_width-1));}
static s16 terrain_view_y(s16 y){if(!WORLD_WRAP_Y)return y;return old_y+(((u16)(y-old_y))&(terrain_height-1));}
static void terrain_change(s16 x,s16 y,u16 old,u16 next,u8 pass) {
 u16 v;
 x=terrain_view_x(x);y=terrain_view_y(y);
 old=backdrop_word(old);next=backdrop_word(next);
 if(x<old_x || x>=old_x+33 || y<old_y || y>=old_y+29 || old==next)return;
 if(!pass){
  v=old&2047;if(v>=16)visible[v-16]--;
  v=next&2047;if(v>=16)visible[v-16]++;
 }else{
  visible_words[((y&31)<<6)|(x&63)]=next;
  v=cached(next);
  VDP_setTileMapData(VDP_getBGBAddress(),&v,((y&31)<<6)|(x&63),1,2,DMA_QUEUE_COPY);
  video_dma_bytes+=2;
 }
}
static void terrain_cell(s16 x,u16 y,u8 pass) {
 const Round *r=&rounds[game.round];u16 original,old,next;
 s16 vy=terrain_view_y(y);
 x=terrain_view_x(x);
 if(x<old_x || x>=old_x+33 || vy<old_y || vy>=old_y+29)return;
 x=(u16)x&(terrain_width-1);
 original=r->map[(y<<(r->width==2048?8:7))+x];
 old=world_override(x,y,bonus_word_state(x,y,original,last_bonus_entered,last_bonus_phases),last_opened);
 next=world_word(x,y,original);
 terrain_change(x,y,old,next,pass);
}
static void palace_torches(void){
 u16 i;u8 changed=0;
 if(game.round!=7 || boss_rush.active)return;
 for(i=0;i<4;i++)if(torch_phase[i]!=bonus_phases[i]){changed|=1<<i;torch_phase[i]=bonus_phases[i];}
 if(!changed)return;
 /* Upload each resident flame texture once, shared by every visible torch.
    Four staggered groups bound DMA work without rewriting the tilemap. */
 for(i=1;i<=torch_tiles[0];i++){
  u16 logical=torch_tiles[i],slot=logical_to_slot[logical];
  if(slot==65535 || !(changed&(1<<(logical&3))))continue;
  terrain_upload_tile(slot,terrain_patterns+(u32)(torch_phase[logical&3]?torch_alternate[logical]:logical)*8);
  video_dma_bytes+=32;
 }
}
static void terrain_state(void){
 u8 i;last_opened=world_opened;last_bonus_entered=bonus_entered;
 for(i=0;i<4;i++)last_bonus_phases[i]=bonus_phases[i];
}
static void terrain_updates(void) {
 const Round *r=&rounds[game.round];const BonusRound *b=&bonus_rounds[game.round];
 u16 i,j,dx,dy,first,last,shift=r->width==2048?7:6,width=r->width>>4;u8 changed=last_opened!=world_opened || last_bonus_entered!=bonus_entered,pass;
 if(!changed && !b->count)return;
 for(i=0;i<4;i++)changed|=last_bonus_phases[i]!=bonus_phases[i];
 if(!changed)return;
 /* Patches are sorted by cell: only visit the visible band of world rows. */
 first=WORLD_WRAP_Y?0:bonus_lower_bound((old_y>>1)<<shift);
 last=WORLD_WRAP_Y?b->count:bonus_lower_bound(((old_y+30)>>1)<<shift);
 /* Every affected cell is visited once; unpin all old patterns before allocation. */
 for(pass=0;pass<2;pass++){
  for(i=0;i<r->patch_count;i++){
   u16 cell=r->patches[i].cell,y=(cell>>shift)*2;
   s16 x=terrain_view_x((cell&(width-1))*2),vy=terrain_view_y(y);
   if(x+2<=old_x || x>=old_x+33 || vy+4<=old_y || vy>=old_y+29)continue;
   if(!((last_opened^world_opened)&(1<<i)) && ((world_opened&(1<<i)) || (!bonus_rows[y>>1] && !bonus_rows[(y+2)>>1])))continue;
   for(dy=0;dy<4;dy++)for(dx=0;dx<2;dx++)terrain_cell(x+dx,y+dy,pass);
  }
  for(i=first;i<last;i++){
   u16 cell=b->patches[i].cell,y=(cell>>shift)*2;
   s16 x=terrain_view_x((cell&(width-1))*2),vy=terrain_view_y(y);
   if(last_bonus_entered==bonus_entered && last_bonus_phases[b->patches[i].bank]==bonus_phases[b->patches[i].bank])continue;
   if(x+2<=old_x || x>=old_x+33 || vy+2<=old_y || vy>=old_y+29)continue;
   for(j=0;j<r->patch_count;j++)if(cell==r->patches[j].cell || cell==r->patches[j].cell+width)break;
   if(j<r->patch_count)continue;
   /* This sorted patch is already known; do not binary-search it twice
      for every 8x8 tile in both passes. World-overlap cases were handled above. */
   {const BonusPatch *p=&b->patches[i];
    const u16 *old=p->words[last_bonus_entered*2+last_bonus_phases[p->bank]];
    const u16 *next=p->words[bonus_entered*2+bonus_phases[p->bank]];
    for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++)
     terrain_change(x+dx,y+dy,old[dy*2+dx],next[dy*2+dx],pass);
   }
  }
 }
 terrain_state();
}
static void scene(u8 full) {
    s16 x = (s16)game.cam_x >> 3, y = (s16)game.cam_y >> 3, xx, yy;
    u16 i;
    if (!full && x == old_x && y == old_y)
        return;
    if (full || x - old_x > MAX_SCROLL_STRIPS || old_x - x > MAX_SCROLL_STRIPS || y - old_y > MAX_SCROLL_STRIPS || old_y - y > MAX_SCROLL_STRIPS) {
        for (i = 0; i < 1800; i++)
            visible[i] = 0;
        for (yy = y; yy < y + 29; yy++)
            pin_row(x, yy, 1);
        for (yy = y; yy < y + 29; yy++) {
            row(x, yy);
            if (full && ((yy - y) & 3) == 3){terrain_upload_flush();DMA_flushQueue();}
        }
    } else if(x-old_x>1 || old_x-x>1 || y-old_y>1 || old_y-y>1) {
        /* Fixed-tick catch-up can cross several terrain rows while falling.
           Update the exposed strips instead of blanking/reloading the level.
           Finish all pin changes before allocating any new VRAM patterns. */
        s16 dx=x>old_x?1:-1,dy=y>old_y?1:-1;
        for(xx=old_x;xx!=x;xx+=dx) {
            pin_column(dx>0?xx:xx+32,old_y,-1);
            pin_column(dx>0?xx+33:xx-1,old_y,1);
        }
        for(yy=old_y;yy!=y;yy+=dy) {
            pin_row(x,dy>0?yy:yy+28,-1);
            pin_row(x,dy>0?yy+29:yy-1,1);
        }
        for(xx=old_x;xx!=x;xx+=dx)column(dx>0?xx+33:xx-1,y);
        for(yy=old_y;yy!=y;yy+=dy)row(x,dy>0?yy+29:yy-1);
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
    terrain_wrapped=x<0 || x+33>terrain_width;
    old_y = y;
}
/* Paired source rows are stored in hardware 32x32 column order. A small
   sprite reads two column spans; aligned bodies need only one DMA request. */
static const u32 *sprite_source(u16 key){
 return object_patterns+((u32)sprite_atlas_blocks[key>>4]<<9)+((key&7)<<6)+((key&8)<<1);
}
/* Counts are 16-pixel units in [0,16]. OR-ing biased counts tests all
   covered bands at once; no per-band branch in the common sprite path. */
static inline u8 sprite_lines_fit(u16 start,u16 end,u8 units){
 const u8 *p=line_count+start;u16 full=0;u8 bias=units-1;
 switch(end-start){
 case 5:full|=p[4]+bias;
 case 4:full|=p[3]+bias;
 case 3:full|=p[2]+bias;
 case 2:full|=p[1]+bias;
 case 1:full|=p[0]+bias;
 }
 return !(full&16);
}
static inline void sprite_lines_add(u16 start,u16 end,u8 units){
 u8 *p=line_count+start;
 switch(end-start){
 case 5:p[4]+=units;
 case 4:p[3]+=units;
 case 3:p[2]+=units;
 case 2:p[1]+=units;
 case 1:p[0]+=units;
 }
}
/* A resident piece must not save the cache-miss/DMA working registers. */
__attribute__((noinline)) static u16 piece_upload(u16 key) {
    u16 slot,i;
        if (sprite_uploads >= 32) {
            video_dropped_sprites++;
            return 65535;
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
            return 65535;
        }
        if(body_keys[slot/4]!=65535 && sprite_slot_for_key[body_keys[slot/4]]==SPR_SLOTS+slot/4)
            sprite_slot_for_key[body_keys[slot/4]]=255;
        body_keys[slot / 4] = 65535;
        if (sprite_keys[slot] != 65535)
            sprite_slot_for_key[sprite_keys[slot]] = 255;
        sprite_keys[slot] = key;
        sprite_slot_for_key[key] = slot;
        {const u32 *source=sprite_source(key);
        VDP_loadTileData(source,SPR_BASE+slot*4,2,DMA_QUEUE);
        VDP_loadTileData(source+32,SPR_BASE+slot*4+2,2,DMA_QUEUE);}
        sprite_uploads++;
        video_dma_bytes += 128;
    return slot;
}
static u8 sprite_palette(u16 code,u8 pal) {
    if(pal==7 && code>=1536)return poison_dragon_palettes[code-1536];
    return pal==3 && code>=1536?black_dragon_palettes[code-1536]:(pal?PAL3:PAL2);
}
static void piece(u16 code, u8 palette, s16 x, s16 y, u8 flip) {
    if(palette==3 && code>=1536 && shop_poison)palette=7;
    u16 key, slot,start,end;
    if (code >= 2048 || sprite_count >= 63 || x <= -16 || x >= 256 || y <= -16 || y >= 224)
        return;
    start=y<0?0:y>>3;end=(y+23)>>3;if(end>28)end=28;
    if(!sprite_lines_fit(start,end,1)){video_dropped_sprites++;return;}
    key = code + palette * 2048;
    slot = sprite_slot_for_key[key];
    if(slot>=SPR_SLOTS){slot=piece_upload(key);if(slot==65535)return;}
    sprite_stamp[slot] = epoch;
    sprite_lines_add(start,end,1);
    VDP_setSpriteFull(sprite_count, x, y, SPRITE_SIZE(2, 2),
                      TILE_ATTR_FULL(sprite_palette(code,palette), TRUE, FALSE, flip, SPR_BASE + slot * 4),
                      sprite_count + 1);
    sprite_count++;
}
/* Assemble non-contiguous body columns directly in the queued DMA buffer.
   Eight tiny VDP transfers otherwise dominate animated enemy cache misses. */
static void sprite_copy_pair(u32 *d,const u32 *s){
 d[0]=s[0];d[1]=s[1];d[2]=s[2];d[3]=s[3];
 d[4]=s[4];d[5]=s[5];d[6]=s[6];d[7]=s[7];
 d[8]=s[8];d[9]=s[9];d[10]=s[10];d[11]=s[11];
 d[12]=s[12];d[13]=s[13];d[14]=s[14];d[15]=s[15];
}
static void body_pieces(u16 code, u8 pal, s16 x, s16 y, u8 flip) {
    piece(code + (flip ? 1 : 0), pal, x, y, flip);
    piece(code + (flip ? 0 : 1), pal, x + 16, y, flip);
    piece(code + (flip ? 9 : 8), pal, x, y + 16, flip);
    piece(code + (flip ? 8 : 9), pal, x + 16, y + 16, flip);
}
/* Keep cache-miss loops and DMA assembly out of the common draw path. */
__attribute__((noinline)) static u16 body_upload(u16 key) {
    u16 block,i,j;
        if (sprite_uploads > 28) {
            return 65535;
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
            return 65535;
        }
        if(body_keys[block]!=65535 && sprite_slot_for_key[body_keys[block]]==SPR_SLOTS+block)
            sprite_slot_for_key[body_keys[block]]=255;
        for (j = 0; j < 4; j++) {
            u16 slot = block * 4 + j;
            if (sprite_keys[slot] != 65535) sprite_slot_for_key[sprite_keys[slot]] = 255;
            sprite_keys[slot] = 65535;
        }
        body_keys[block] = key;
        if(!(key&8) && (key&7)!=7){
            VDP_loadTileData(sprite_source(key),SPR_BASE+block*16,16,DMA_QUEUE);
        }else{
            u32 *tiles=DMA_allocateAndQueueDma(DMA_VRAM,(SPR_BASE+block*16)*32,256,2);
            if(!tiles){body_keys[block]=65535;video_dropped_sprites++;return 65534;}
            for(j=0;j<4;j++){
                sprite_copy_pair(tiles+j*32,sprite_source(key+(j>>1))+(j&1)*32);
                sprite_copy_pair(tiles+j*32+16,sprite_source(key+8+(j>>1))+(j&1)*32);
            }
        }
        sprite_uploads += 4;
        video_dma_bytes += 512;
    return block;
}
static void body(u16 code, u8 pal, s16 x, s16 y, u8 flip) {
    if(pal==3 && code>=1536 && shop_poison)pal=7;
    u16 key = code + pal * 2048, block, start, end;
    if (code > 2038 || sprite_count >= 63 || x <= -32 || x >= 256 || y <= -32 || y >= 224)
        return;
    start = y < 0 ? 0 : y >> 3;
    end = (y + 39) >> 3;
    if (end > 28) end = 28;
    if(!sprite_lines_fit(start,end,2)){
        body_pieces(code,pal,x,y,flip);return;
    }
    /* Share the direct key index: 0..79 are pieces, 80..99 are bodies.
       A displaced format is a cache miss, never a stale VRAM reference. */
    block=sprite_slot_for_key[key];
    if(block>=SPR_SLOTS && block<SPR_SLOTS+SPR_SLOTS/4)block-=SPR_SLOTS;
    else block=SPR_SLOTS/4;
    if(block==SPR_SLOTS/4){
        block=body_upload(key);
        if(block>=65534){if(block==65535)body_pieces(code,pal,x,y,flip);return;}
    }
    sprite_slot_for_key[key]=SPR_SLOTS+block;
    body_stamp[block] = epoch;
    sprite_lines_add(start,end,2);
    VDP_setSpriteFull(sprite_count, x, y, SPRITE_SIZE(4, 4),
                      TILE_ATTR_FULL(sprite_palette(code,pal), TRUE, FALSE, flip, SPR_BASE + block * 16),
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
    } else if (game.mode==CLEAR || p->exploration || !p->invincible || (game.frame & 4)) {
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
            /* Cull before calling family-specific frame selectors. Actors keep
               simulating off-screen; their invisible art needs no CPU work. */
            s16 width=visual->layout==DRAW_DRAGON?128:visual->layout==DRAW_WAVE?64:32;
            s16 height=visual->layout>=DRAW_DRAGON?64:32;
            if(x<=-width || x>=256 || y<=-height || y>=224)continue;
            if(visual->frame){
                const AnimFrame *f=visual->frame(i);
                if(f){
                    if(visual->layout==DRAW_PIECE)piece(f->code,f->palette,x,y,f->flip);
                    else if(visual->layout==DRAW_BODY)body(f->code,f->palette,x,y,f->flip);
                    else{
                        u16 col,row,columns=visual->layout==DRAW_DRAGON?8:4;
                        u8 palette=visual->layout==DRAW_DRAGON && f->palette==7?dragon_kinds[a->def]:f->palette;
                        /* One 32x32 SAT entry replaces four 16x16 entries, using
                           the same source cells and whole-body flip order. */
                        for(row=0;row<4;row+=2)for(col=0;col<columns;col+=2)
                            body(f->code+row*8+(f->flip?columns-2-col:col),palette,x+col*16,y+row*16,f->flip);
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
    if(skeleton_weapons_occupied || game.mode!=PLAY)for (i = 0; i < MAX_ACTORS; i++) {
        s16 wx, wy;
        const AnimFrame *f = skeleton_weapon_frame(i, &wx, &wy);
        if (f)
            piece(f->code, f->palette, wx - game.cam_x, wy - game.cam_y, f->flip);
    }
    if(edge_shots_occupied || game.mode!=PLAY)for(i=0;i<24;i++){const AnimFrame *f;if(!edge_shots[i].active)continue;f=edge_shot_frame(i);if(f)piece(f->code,f->palette,edge_shots[i].x-game.cam_x,edge_shots[i].y-game.cam_y,f->flip);}
    if(reinforcement_shots_occupied || game.mode!=PLAY)for(i=0;i<24;i++){const AnimFrame *f;if(!reinforcement_shots[i].active)continue;f=reinforcement_shot_frame(i);if(f)piece(f->code,f->palette,reinforcement_shots[i].x-game.cam_x,reinforcement_shots[i].y-game.cam_y,f->flip);}
    if(flailer_weapons_occupied || game.mode!=PLAY)for(i=0;i<(flailer_weapons_occupied?flailer_weapons_occupied:MAX_ACTORS);i++){const AnimFrame *f;if(!flailer_weapons[i].active)continue;f=flailer_weapon_frame(i);if(f)piece(f->code,f->palette,flailer_weapons[i].x-game.cam_x,flailer_weapons[i].y-game.cam_y,f->flip);}
    if(dragon_shots_occupied || game.mode!=PLAY)for(i=0;i<24;i++){const AnimFrame *f;if(!dragon_shots[i].active)continue;f=dragon_shot_frame(i);DragonShot *p=&dragon_shots[i];if(f){if(p->kind==2)body(f->code,f->palette,p->x-game.cam_x,p->y-game.cam_y,f->flip);else piece(f->code,f->palette,p->x-game.cam_x,p->y-game.cam_y,f->flip);}}
    if(waveboss_seeds_occupied || game.mode!=PLAY)for(i=0;i<MAX_WAVEBOSS_SEEDS;i++){const AnimFrame *f;if(!waveboss_seeds[i].active)continue;f=waveboss_seed_frame(i);if(f)piece(f->code,f->palette,waveboss_seeds[i].x-game.cam_x,waveboss_seeds[i].y-game.cam_y,f->flip);}
    if(container_traps_occupied || game.mode!=PLAY)for(i=0;i<(container_traps_occupied?container_traps_occupied:MAX_CONTAINER_TRAPS);i++){const AnimFrame *f;if(!container_traps[i].active)continue;f=container_trap_frame(i);if(f)piece(f->code,f->palette,container_traps[i].x-game.cam_x,container_traps[i].y-game.cam_y,f->flip);}
    if(shell_pools_occupied[0] || shell_pools_occupied[1] || game.mode!=PLAY)for(i=0;i<MAX_STATUE_SHELLS;i++) {
        const AnimFrame *f=hunter_shells[i].active?hunter_shell_frame(&hunter_shells[i]):0;
        if(f)piece(f->code,f->palette,hunter_shells[i].x-game.cam_x,hunter_shells[i].y-game.cam_y,f->flip);
        f=hunter_blasts[i].active?hunter_shell_frame(&hunter_blasts[i]):0;
        if(f)body(f->code,f->palette,hunter_blasts[i].x-game.cam_x,hunter_blasts[i].y-game.cam_y,f->flip);
        f=statue_shells[i].active?statue_shell_frame(&statue_shells[i]):0;
        if(f)piece(f->code,f->palette,statue_shells[i].x-game.cam_x,statue_shells[i].y-game.cam_y,f->flip);
        f=statue_blasts[i].active?statue_shell_frame(&statue_blasts[i]):0;
        if(f)body(f->code,f->palette,statue_blasts[i].x-game.cam_x,statue_blasts[i].y-game.cam_y,f->flip);
    }
    if(missiles_occupied || game.mode!=PLAY)for(i=0;i<(missiles_occupied?missiles_occupied:MAX_MISSILES);i++){const AnimFrame *f;if(!missiles[i].active)continue;f=missile_frame(i);if(f)piece(f->code,f->palette,missiles[i].x-game.cam_x,missiles[i].y-game.cam_y,f->flip);}
    for(i=0;i<pot_puffs_end;i++)if(pot_puffs[i].active){const AnimFrame *f=animation_current(&pot_puffs[i].animation,pot_segments[pot_puff].clip);if(f)body(f->code,f->palette,pot_puffs[i].x-game.cam_x,pot_puffs[i].y-game.cam_y,f->flip);}
    for(i=0;i<pots_end;i++){const AnimFrame *f=pot_frame(i);if(f)piece(f->code,f->palette,pots[i].x-game.cam_x,pots[i].y-game.cam_y,f->flip);}
    for (i = 0; i < loot_active_end; i++) {
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
            body(f->code, f->palette, world_near_x(sp->x) - 8 - game.cam_x, world_near_y(sp->y) - 8 - game.cam_y, f->flip);
        }
    }
    if(arena_video_active)sprite_count=arena_video_columns(sprite_count,line_count);
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
    VDP_drawTextEx(BG_A,s,TILE_ATTR(PAL3,TRUE,FALSE,FALSE),arena_video_text_x(x,y),y,DMA_QUEUE);
}
static u8 last_shop = 255,last_npc_page=255,last_credits=255;
static void digits(char *p, u16 v, u16 count) {
    while (count) {
        p[--count] = '0' + v % 10;
        v /= 10;
    }
}
static void overlay(void) {
    u8 m = game.mode, changed = m != last_mode || (m==CLEAR && last_clear_phase!=round_clear.phase);
    if(m==GAMEOVER && last_credits!=frontend.credits)changed=1;
    last_credits=frontend.credits;
    if(m==GAMEOVER && (last_game_over_phase!=game_over.phase || last_continue_digit!=game_over.digit))changed=1;
    last_game_over_phase=game_over.phase;last_continue_digit=game_over.digit;
    last_clear_phase=round_clear.phase;
    char b[40];
    if (changed) {
        if(!clear_screen_active && !ending_screen_active){
            VDP_clearPlane(BG_A, TRUE);
            if(arena_video_active)arena_video_restore(0);
        }
        ui_hud_invalidate();
        last_mode = m;
    }
    if(!clear_screen_active && !ending_screen_active)ui_hud();
    VDP_setTextPlane(BG_A);
    if(m==RESCUE && (changed || last_npc_page!=npc_sequence.page)) {
        u16 i,tiles[128];const u16 *page=npc_dialogue();
        if(changed){
            VDP_loadTileData(npc_dialogue_font,1408,NPC_FONT_TILES>32?32:NPC_FONT_TILES,DMA);
#if NPC_FONT_TILES > 32
            VDP_loadTileData(npc_dialogue_font+32*8,1072,NPC_FONT_TILES>48?16:NPC_FONT_TILES-32,DMA);
#endif
#if NPC_FONT_TILES > 48
            VDP_loadTileData(npc_dialogue_font+48*8,1,NPC_FONT_TILES-48,DMA);
#endif
        }
        for(i=0;i<128;i++)tiles[i]=npc_dialogue_glyphs[page[i]];
        VDP_setTileMapDataRectEx(BG_A,tiles,0,0,6,32,4,32,CPU);
        last_npc_page=npc_sequence.page;
    }

    if (!changed && !(m == SHOP && last_shop != game.shop_item))
        return;
    last_shop = game.shop_item;
    if (m == TITLE) {
        text(9, 7, "BLACK TIGER");
        text(7, 10, "SGDK DEVELOPMENT BUILD");
        text(10, 14, "PRESS START");
        text(8, 18, "A ATTACK  B JUMP");
        text(4, 20, "RESCUE OLD MEN FOR SHOPS");
    } else if (m == PAUSED)
        text(13, 12, "PAUSED");
    else if (m == SHOP) {
        /* The arcade panel is handled by shop_video_frame. */
    } else if (m == CLEAR) {
        /* The source bonus artwork is installed by video_frame. */
    } else if (m == GAMEOVER) {
        text(11, 10, "GAME OVER");
        if(game_over.phase==2) {
            text(10,12,"CONTINUE? 0");b[0]='0'+game_over.digit;b[1]=0;text(20,12,b);
            text(8,14,frontend.credits?(frontend.mode?"START TO CONTINUE":"A TO CONTINUE    "):"START TO ADD COIN");
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
    u32 upload_buffer[32*8];
    u32 *previous_upload=terrain_upload;terrain_upload=upload_buffer;
    video_reload_count++;
    terrain_backdrop=backdrop_for_round(game.round);
    terrain_width=rounds[game.round].width>>3;
    terrain_height=rounds[game.round].height>>3;
    terrain_shift=rounds[game.round].width==2048?8:7;
    terrain_map=boss_rush.active?arena_video_map():rounds[game.round].map;
    terrain_patterns=boss_rush.active?arena_video_pattern(0):rounds[game.round].patterns;
    terrain_slots=terrain_backdrop?(game.round==3?640:684):boss_rush.active?828:BG_SLOTS;
    shop_screen_active=0;
    clear_screen_active=ending_screen_active=0;
    terrain_state();
    u16 i;for(i=0;i<4;i++)torch_phase[i]=bonus_phases[i];
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
    PAL_setColors(32, object_palette, 32, CPU);poison_palette_active=0; /* SGDK font uses foreground pen 15. */
    PAL_setColor(63, 0xeee);
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    VDP_clearPlane(WINDOW, TRUE);
    for (i = 0; i < 2; i++)
        VDP_fillTileMapRect(WINDOW, TILE_ATTR_FULL(PAL2, TRUE, FALSE, FALSE, 0), 0, i, 32, 1);
    if(boss_rush.active || terrain_backdrop){arena_video_init();if(!boss_rush.active)scene(1);old_x=(s16)game.cam_x>>3;old_y=(s16)game.cam_y>>3;}
    else {arena_video_reset();scene(1);}
    terrain_upload_flush();DMA_flushQueue();
    terrain_upload=previous_upload;
    last_round = game.round;
    last_mode = 255;
    ui_game_init();
    VDP_setEnable(TRUE);
    SYS_enableInts();
}
static void bonus_screen(void) {
    /* This replaces the terrain cache only after the victory animation ends. */
    SYS_disableInts();
    VDP_setEnable(FALSE);
    DMA_flushQueue();
    if(arena_video_active)arena_video_reset();
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
        if(arena_video_active)arena_video_reset();
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
extern u8 profile_frame;
volatile u16 video_cost[3];
void video_frame(void) {
    u32 upload_buffer[32*8];terrain_upload=upload_buffer;
    u32 t = profile_frame?getSubTick():0;
    video_dma_bytes = 0;
    if(arena_video_active && (game.mode==TITLE || game.mode==INTRO))arena_video_reset();
    else if(arena_video_active && game.round!=last_round)video_round();
    if(game.mode==TITLE){ui_title();if(profile_frame){video_cost[0]=getSubTick()-t;video_cost[1]=video_cost[2]=0;}last_mode=TITLE;return;}
    if(game.mode==INTRO){intro_video();last_mode=INTRO;return;}
    if(last_mode==TITLE || last_mode==INTRO)video_round();
    if(game.mode==ENDING || (game.mode==GAMEOVER && ending.complete)) {
        ending_screen();overlay();
        if(profile_frame){video_cost[0]=getSubTick()-t;video_cost[1]=video_cost[2]=0;}return;
    }
    if(shop_screen_active && game.mode!=SHOP)video_round();
    if(game.mode==SHOP){
        if(poison_palette_active){PAL_setColors(39,object_palette+7,4,CPU);poison_palette_active=0;}
        if(!shop_screen_active){if(arena_video_active)arena_video_reset();shop_video_init();shop_screen_active=1;}
        shop_video_frame();last_mode=SHOP;
        if(profile_frame){video_cost[0]=getSubTick()-t;video_cost[1]=video_cost[2]=0;}return;
    }
    if(ending_screen_active)video_round();
    if(game.mode==CLEAR && round_clear.phase==2 && game.round<7) {
        if(clear_screen_active!=game.round+1)bonus_screen();
        overlay();
        if(profile_frame){video_cost[0]=getSubTick()-t;video_cost[1]=video_cost[2]=0;}
        return;
    }
    if(clear_screen_active)video_round();
    if (last_round != game.round || ((s16)game.cam_x >> 3) - old_x > MAX_SCROLL_STRIPS ||
        old_x - ((s16)game.cam_x >> 3) > MAX_SCROLL_STRIPS || ((s16)game.cam_y >> 3) - old_y > MAX_SCROLL_STRIPS ||
        old_y - ((s16)game.cam_y >> 3) > MAX_SCROLL_STRIPS)
        video_round();
    if(boss_rush.active){arena_video_frame();old_x=(s16)game.cam_x>>3;old_y=(s16)game.cam_y>>3;}
    else {palace_torches();terrain_updates();scene(0);if(arena_video_active)arena_video_frame();}
    terrain_upload_flush();
    if(profile_frame){u32 now=getSubTick();video_cost[0]=now-t;t=now;}
    if(!arena_video_active){VDP_setHorizontalScrollVSync(BG_B, -game.cam_x);
    VDP_setVerticalScrollVSync(BG_B, game.cam_y);}
    /* Source fixed 195C changes skin only, never transparency or terrain colors. */
    {u8 poisoned=shop_poison!=0;
    if(poisoned!=poison_palette_active){
        PAL_setColors(39,poisoned?poison_skin_palette:object_palette+7,4,DMA_QUEUE);
        video_dma_bytes+=8;poison_palette_active=poisoned;
    }
    }
    sprites();
    if(profile_frame){u32 now=getSubTick();video_cost[1]=now-t;t=now;}
    overlay();
    if(profile_frame)video_cost[2]=getSubTick()-t;
}
