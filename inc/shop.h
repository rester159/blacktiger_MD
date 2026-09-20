#ifndef SHOP_H
#define SHOP_H
#include "game.h"
extern volatile u8 shop_difficulty;
extern u8 shop_antidotes,shop_poison;
typedef struct {u16 coins,invincible;u8 weapon,armor,keys,antidotes,poison;} ShopInventory;
u16 shop_price(u8 item,u8 difficulty);
u8 shop_purchase(u8 item,u8 difficulty,ShopInventory *state);
u8 shop_buy(u8 item);
void shop_new(void);
void shop_move(u16 pressed);
#endif
