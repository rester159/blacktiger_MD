#ifndef CRAWLER_H
#define CRAWLER_H
#include "animation.h"
typedef struct {const AnimClip *clip;u16 next;u8 event;} CrawlerSegment;
void crawler_spawn(u16 slot,u8 part);
void crawler_screen_attack(u16 slot);
void crawler_step(u16 slot);
u8 crawler_hit(u16 slot,u8 damage);
u8 crawler_vulnerable(u16 slot);
u8 crawler_contact(u16 slot);
const AnimFrame *crawler_frame(u16 slot);
#endif
