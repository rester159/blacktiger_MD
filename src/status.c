#include "status.h"
#include "shop.h"
u8 status_reverse,status_gate;
void status_new(void) {status_reverse=status_gate=0;}
void status_tick(void) {if(status_gate)status_gate--;}
void status_poison_contact(void) {
 if(status_gate)return;
 if(shop_antidotes){shop_antidotes--;status_gate=30;}
 else {shop_poison=0x26;status_gate=60;}
}
u8 status_poison_cloud_contact(void){u8 hurt=!status_gate && !shop_antidotes;status_poison_contact();return hurt;}
void status_reverse_contact(void) {
 if(status_gate)return;
 if(shop_antidotes){shop_antidotes--;status_gate=30;}
 else {status_reverse^=1;status_gate=60;}
}
u16 status_controls(u16 input) {
 if(status_reverse)input=(input&~(IN_LEFT|IN_RIGHT))|((input&IN_LEFT)<<1)|((input&IN_RIGHT)>>1);
 return input;
}
