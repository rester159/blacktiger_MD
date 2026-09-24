#include "backdrop.h"
#include "backdrop_data.inc"
const Backdrop *backdrop_for_round(u8 round){
 switch(round){case 4:return &backdrop_4;case 6:return &backdrop_6;default:return 0;}
}

const u32 *backdrop_hud_patterns(void){return backdrop_hud;}
void backdrop_hud_edge_load(u16 x,u16 tile){
 const u16 *edge=backdrop_hud_edges+((u16)backdrop_hud_edge_index[x&255]<<3);
 u32 *tiles=DMA_allocateAndQueueDma(DMA_VRAM,tile*32,128,2);u16 i;
 if(!tiles)return;
 /* Expand deduplicated tiles with plain longword copies. One queued transfer
    avoids eight DMA setups while retaining the compact cartridge layout. */
 for(i=0;i<8;i++){
  const u32 *s=backdrop_hud_edge_tiles+(u32)edge[i]*8;u32 *d=tiles+i*8;
  d[0]=s[0];d[1]=s[1];d[2]=s[2];d[3]=s[3];
  d[4]=s[4];d[5]=s[5];d[6]=s[6];d[7]=s[7];
 }

}
