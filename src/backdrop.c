#include "backdrop.h"
#include "backdrop_data.inc"
const Backdrop *backdrop_for_round(u8 round){
 switch(round){case 3:return &backdrop_3;case 5:return &backdrop_5;case 6:return &backdrop_6;default:return 0;}
}
