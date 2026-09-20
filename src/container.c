#include "container.h"
#include "assets.h"
#include "loot.h"
static u8 container_contents[8],container_round_id=255;
static u8 rotate(u8 value) {return (value>>1)|(value<<7);}
u16 container_shuffle(u8 round,u16 seed,u8 *out) {
 u16 i;for(i=0;i<8;i++)out[i]=container_initial[round][i];
 for(i=0;i<8;i++) {
  u8 a=rotate(seed>>8)&7,b=rotate((u8)(rotate(seed>>8)+(u8)seed))&7,t=out[a];
  out[a]=out[b];out[b]=t;
  /* The source yields for two frame updates between swaps. */
  seed=(seed<<1)+seed+(seed<<8);
  seed=(seed<<1)+seed+(seed<<8);
 }
 return seed;
}
void container_new(void) {container_round_id=255;}
void container_round(u8 round) {
 if(round!=container_round_id) {
  container_round_id=round;loot_random=container_shuffle(round,loot_random,container_contents);
 }
}
u8 container_content(u8 persistent) {return persistent>=33 && persistent<41?container_contents[persistent-33]-16:0;}

u8 container_contact(u8 content,ContainerContact *s) {
 if(content>=6)return CONTAINER_NO_CONTACT;
 if(content==0 || !s->opened) {
  if(!s->keys)return CONTAINER_NO_CONTACT;
  --s->keys;s->opened=1;
  if(content==0) {s->collected=1;return CONTAINER_TRAP;}
  return CONTAINER_OPEN;
 }
 s->collected=1;
 if(content==5) {s->hp=s->max_hp;s->invincible=0;}
 else s->coins+=container_coin_values[content-1];
 return CONTAINER_COLLECT;
}
