#include "large_contact.h"
/* Original large sprites use 16-bit screen coordinates and asymmetric negative
   bounds. Preserve wrapping at the screen edges instead of signed abs(). */
static u16 separation(u16 point,u16 origin,u8 carry){
 u16 delta=point-origin-carry;
 return (u32)point<(u32)origin+carry?(u16)(1-delta):delta;
}
static u16 weak_axis(u16 point,s8 offset,u16 origin,u8 dagger){
 u16 shifted=point-(u16)(s16)offset;
 return separation(shifted,origin,dagger && point<(u16)(s16)offset);
}
u8 large_weapon_contact(const LargeContactShape *s,s16 ax,s16 ay,s16 x,s16 y,u8 w,u8 h,u8 dagger){
 u16 px=(u16)x-24,py=(u16)y-24;
 if(weak_axis(px,s->weak_x,ax,dagger)<=s->weak_width+w && weak_axis(py,s->weak_y,ay,dagger)<=s->weak_height+h)return 2;
 if(separation(px,ax,dagger && (u16)x<24)<=s->body_width+w && separation(py,ay,0)<=s->body_height+h)return 1;
 return 0;
}
u8 large_player_contact(const LargeContactShape *s,s16 ax,s16 ay,s16 x,s16 y,u8 w,u8 h,u8 alternate){
 u16 px=(u16)((u8)x-16),py=alternate?(u8)y+20:(u16)((u8)y-16);
 return separation(px,ax,0)<=w+(alternate?3:s->body_width) && separation(py,ay,0)<=h+(alternate?6:s->body_height);
}
/* Eight-column dragons use a different X origin. Only dagger weak-Y retains carry. */
u8 wide_weapon_contact(const LargeContactShape *s,s16 ax,s16 ay,s16 x,s16 y,u8 w,u8 h,u8 dagger){
 u16 px=(u16)x-56,py=(u16)y-24;
 if(weak_axis(px,s->weak_x,ax,0)<=s->weak_width+w && weak_axis(py,s->weak_y,ay,dagger)<=s->weak_height+h)return 2;
 if(separation(px,ax,0)<=s->body_width+w && separation(py,ay,0)<=s->body_height+h)return 1;
 return 0;
}
u8 wide_player_contact(const LargeContactShape *s,s16 ax,s16 ay,s16 x,s16 y,u8 w,u8 h,u8 alternate){
 u16 px=(u16)((u8)x-48),py=alternate?(u8)y+26:(u16)((u8)y-16);
 return separation(px,ax,0)<=w+(alternate?3:s->body_width) && separation(py,ay,0)<=h+(alternate?3:s->body_height);
}
