#include "boot_logos.h"
#include "sega_logo_shinobi.h"
#include "capcom_logo.h"
extern const u8 sega_chant_pcm[27136];
void boot_pcm_init(void);
void boot_pcm_idle(void);
volatile u16 boot_stage,boot_tick;
volatile u8 boot_done;
static const u16 black[64]={0};
/* Boot owns the display and sound until teardown, before game initialization. */
static void clear_screen(void){
 VDP_setEnable(FALSE);DMA_flushQueue();PAL_setColors(0,black,64,CPU);
 VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);VDP_clearPlane(WINDOW,TRUE);
 VDP_setHorizontalScroll(BG_A,0);VDP_setHorizontalScroll(BG_B,0);
 VDP_setVerticalScroll(BG_A,0);VDP_setVerticalScroll(BG_B,0);
 VDP_setWindowVPos(FALSE,0);VDP_setWindowHPos(FALSE,0);
 VDP_setBackgroundColor(0);
}
static u8 wait_frame(void){SYS_doVBlankProcess();return !!(JOY_readJoypad(JOY_1)&BUTTON_START);}
void boot_logos(void){
 u16 i,phase=0;u8 skip=0,chant=0,pal=SYS_isPAL();
 boot_done=0;boot_stage=0;boot_tick=0;
 boot_pcm_init();
 VDP_setScreenWidth256();VDP_setPlaneSize(64,32,TRUE);clear_screen();
 VDP_loadTileData(shinobi_logo_tiles,16,SHINOBI_LOGO_TILE_COUNT,DMA);
 /* Original H40 artwork centered in the game's H32 viewport. */
 for(i=0;i<48;i++)VDP_setTileMapXY(BG_A,17+i,10+i%12,10+i/12);
 shinobi_palroll_reset();PAL_setColors(0,shinobi_logo_cram,16,CPU);VDP_setEnable(TRUE);
 boot_stage=1;
 while(boot_tick<SHINOBI_LOGO_HOLD_FRAMES){
  u8 steps=1;if(wait_frame()){skip=1;break;}
  if(pal && ++phase==5){phase=0;steps=2;}
  while(steps-- && boot_tick<SHINOBI_LOGO_HOLD_FRAMES){shinobi_palroll_step();boot_tick++;}
  if(!chant && boot_tick>=24){
   SND_PCM_startPlay(sega_chant_pcm,sizeof sega_chant_pcm,SOUND_PCM_RATE_16000,SOUND_PAN_CENTER,FALSE);chant=1;
  }
  PAL_setColors(0,shinobi_logo_cram,16,CPU);
 }
 SND_PCM_stopPlay();Z80_unloadDriver();
 Z80_requestBus(TRUE);YM2612_reset();
 clear_screen();
 if(!skip){
  boot_stage=2;boot_tick=0;phase=0;
  capcom_intro_reset();
  capcom_logo_draw(16,10,12);PAL_setColors(0,capcom_logo_cram,16,CPU);VDP_setEnable(TRUE);
  while(boot_tick<CAPCOM_INTRO_FRAMES){
   u8 steps=1;if(wait_frame()){skip=1;break;}
   if(pal && ++phase==5){phase=0;steps=2;}
   while(steps-- && boot_tick<CAPCOM_INTRO_FRAMES){capcom_intro_step();boot_tick++;}
   PAL_setColors(0,capcom_logo_cram,16,CPU);
  }
  /* Stop all jingle state and restore SGDK's driver before native game audio. */
 }
 YM2612_reset();Z80_releaseBus();boot_pcm_idle();
 clear_screen();VDP_setEnable(TRUE);
 /* Consume Start so skipping cannot accidentally choose a title-menu item. */
 while(JOY_readJoypad(JOY_1)&BUTTON_START)SYS_doVBlankProcess();
 boot_stage=3;boot_done=1;
}
