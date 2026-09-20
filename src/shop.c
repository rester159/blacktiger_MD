#include "shop.h"
#include "status.h"
#include "assets.h"
#include "container.h"
/* Prevent GCC 16 LTO from widening the masked byte load to an odd-address long. */
volatile u8 shop_difficulty;
u8 shop_antidotes,shop_poison;
void shop_new(void) {status_new();shop_difficulty=shop_default_difficulty;shop_antidotes=shop_poison=0;}
u16 shop_price(u8 item,u8 difficulty) {
 if(item>=1 && item<=8)return shop_prices[(item-1)>>2][difficulty&7][(item-1)&3];
 return item==9?shop_key_price:item==10?shop_antidote_price:0;
}
u8 shop_purchase(u8 item,u8 difficulty,ShopInventory *s) {
 u16 price=shop_price(item,difficulty);
 if(item<1 || item>10 || s->coins<price)return 0;
 if(item<=4) {if(s->weapon>=item)return 0;s->weapon=item;}
 else if(item<=8) {u8 armor=(item-4)*2;if(s->armor>=armor)return 0;s->armor=armor;}
 else if(item==9) {if(s->keys==99)return 0;s->keys++;}
 else {
  if(s->antidotes==99)return 0;
  if(s->poison) {s->poison=0;s->invincible=0;}
  else s->antidotes++;
 }
 s->coins-=price;return 1;
}
u8 shop_buy(u8 item) {
 ShopInventory s;
 s.coins=game.coins;s.invincible=game.p.invincible;s.weapon=game.p.weapon?game.p.weapon-1:0;
 s.armor=game.p.armor;s.keys=container_keys;s.antidotes=shop_antidotes;s.poison=shop_poison || status_reverse;
 if(!shop_purchase(item,shop_difficulty,&s))return 0;
 game.coins=s.coins;game.p.invincible=s.invincible;game.p.weapon=s.weapon+1;game.p.armor=s.armor;
 container_keys=s.keys;shop_antidotes=s.antidotes;if(item==10 && !s.poison){shop_poison=0;status_reverse=0;}game.sound=SND_BUY;return 1;
}
void shop_move(u16 pressed) {
 u8 column=game.shop_item/6,row=game.shop_item%6;
 if(pressed&IN_LEFT)column=0;
 if(pressed&IN_RIGHT)column=1;
 if((pressed&IN_UP) && row)row--;
 if((pressed&IN_DOWN) && row<5)row++;
 if(!column && row>4)row=4;
 game.shop_item=column*6+row;
}
