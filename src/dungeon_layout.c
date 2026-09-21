#include "dungeon.h"
#include "dungeon_layout.h"
#include "assets.h"
#include "dungeon_chunks.inc"
DungeonLayout dungeon_layout;
Round dungeon_round;
static Spawn generated_spawns[40];
static u16 choose(u32 *stream,u16 count){return dungeon_rng(stream)%count;}
void dungeon_generate(void){
 static const u8 lengths[4]={6,7,8,10};
 /* Independently drawn source theme and population; all chunks in a stage
    share the original background art bank, avoiding palette degradation. */
 static const u8 enemies[]={1,24,52}; /* established skeleton controllers */
 u8 i,act=(dungeon.stage-1)>>2,n=0,source=choose(&dungeon.streams[2],8);
 u8 first=dungeon_chunk_start[source],count=dungeon_chunk_start[source+1]-first;
 dungeon_layout=(DungeonLayout){.ready=1,.count=lengths[act],.source=source};
 for(i=0;i<dungeon_layout.count;i++){
  u8 choices[15],nchoices=0,id,j;
  for(j=first;j<first+count;j++){
   if(i){u16 pair=dungeon_layout.ids[i-1]*(sizeof dungeon_chunks/sizeof dungeon_chunks[0])+j;
    if(j==dungeon_layout.ids[i-1] || !(dungeon_pair_ok[pair>>3]&(1<<(pair&7))))continue;
   }
   choices[nchoices++]=j;
  }
  id=nchoices?choices[choose(&dungeon.streams[0],nchoices)]:dungeon_layout.ids[i-1];
  dungeon_layout.ids[i]=id;
 }
 dungeon_round=rounds[source];dungeon_round.width=(u16)dungeon_layout.count*256;
 dungeon_round.height=1024;dungeon_round.start_x=0;dungeon_round.start_y=528;
 dungeon_round.patch_count=0;dungeon_round.spawns=generated_spawns;
 dungeon_layout.exit_x=dungeon_round.width-48;
 for(i=0;i<dungeon_layout.count;i++){
  const DungeonChunk *c=&dungeon_chunks[dungeon_layout.ids[i]];
  u8 a=choose(&dungeon.streams[1],c->anchor_count);
  u16 x=(u16)i*256+c->anchors[a];
  /* Reserve the first screen for a safe spawn. Merchants replace an enemy
     in two separate chunks, so the route always includes a store. */
  if(!i)continue;
  if(i==1 || i==dungeon_layout.count-2){generated_spawns[n++]=(Spawn){x,DUNGEON_FLOOR-32,9,71};continue;}
  generated_spawns[n++]=(Spawn){x,DUNGEON_FLOOR-32,enemies[choose(&dungeon.streams[1],3)],71};
  if(act && c->anchor_count>1){u8 other=(a+1)%c->anchor_count;u16 bx=(u16)i*256+c->anchors[other];
   if(bx+48<x || bx>x+48)generated_spawns[n++]=(Spawn){bx,DUNGEON_FLOOR-32,enemies[choose(&dungeon.streams[1],3)],71};
  }
 }
 dungeon_round.spawn_count=n;
}
u8 dungeon_terrain(s16 x,s16 y){
 const Round *r=&rounds[dungeon_layout.source];const DungeonChunk *c;
 u16 sx,sy;
 if(x<0 || x>=dungeon_round.width || y<DUNGEON_TOP)return 3;
 if(y>=DUNGEON_TOP+224)return 3;
 c=&dungeon_chunks[dungeon_layout.ids[(u16)x>>8]];
 sx=(u16)c->x+((x&255)>>4);sy=(u16)c->y+((y-DUNGEON_TOP)>>4);
 return r->collision[(sy<<(r->width==2048?7:6))+sx];
}
u16 dungeon_word(u16 x,u16 y){
 const Round *r=&rounds[dungeon_layout.source];const DungeonChunk *c;
 u16 sx,sy;
 if(x>=dungeon_round.width/8 || y<DUNGEON_TOP/8 || y>=(DUNGEON_TOP+224)/8)return 0;
 c=&dungeon_chunks[dungeon_layout.ids[x>>5]];
 sx=(u16)c->x*2+(x&31);sy=(u16)c->y*2+y-DUNGEON_TOP/8;
 return r->map[(sy<<(r->width==2048?8:7))+sx];
}
void dungeon_checkpoint(u16 x,u16 *px,u16 *py){
 u16 chunk=x>>8;if(chunk>=dungeon_layout.count)chunk=dungeon_layout.count-1;
 *px=chunk*256;*py=DUNGEON_FLOOR-32;
}
