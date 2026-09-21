#include "game.h"
#include "frontend.h"
#include <genesis.h>
volatile u16 frame_cost[3], early_vblank_flushes, vblank_flush_overruns;
int main(bool hardReset) {
    u16 pal_phase = 0;
    u32 last_presented=0xffffffff;
    (void)hardReset;
    JOY_init();
    video_init();
    frontend_init();
    game_new();
    game.mode = TITLE;
    video_round();
    while (TRUE) {
        u16 joy = JOY_readJoypad(JOY_1), in = 0;
        if (joy & BUTTON_LEFT)
            in |= IN_LEFT;
        if (joy & BUTTON_RIGHT)
            in |= IN_RIGHT;
        if (joy & BUTTON_UP)
            in |= IN_UP;
        if (joy & BUTTON_DOWN)
            in |= IN_DOWN;
        if (joy & BUTTON_B)
            in |= IN_JUMP;
        if (joy & BUTTON_A)
            in |= IN_ATTACK;
        if (joy & BUTTON_START)
            in |= IN_START;
        if (joy & BUTTON_MODE)in |= IN_COIN;
        u32 t0 = getSubTick();
        game_tick(in);
        frame_cost[0] = getSubTick() - t0; /* PAL maintains the same 60 Hz rule clock. */
        if (SYS_isPAL() && ++pal_phase == 5) {
            game_tick(in);
            pal_phase = 0;
        }
        t0 = getSubTick();
        video_frame();
        frame_cost[1] = getSubTick() - t0;
        t0 = getSubTick();
        audio_tick();
        frame_cost[2] = getSubTick() - t0;
        /* A small queue finishing just after VBlank starts can still be
           presented this frame. Counter <=230 leaves at least 26 NTSC lines
           (including its counter discontinuity) for a <=1.5 KiB queue and SGDK
           housekeeping. Never process twice in the same VBlank. */
        if(!SYS_isPAL() && vtimer!=last_presented &&
           GET_VDP_STATUS(VDP_VBLANK_FLAG) && GET_VCOUNTER<=230 &&
           GET_VCOUNTER>=224 && DMA_getQueueTransferSize()<=1536) {
            SYS_doVBlankProcessEx(ON_VBLANK);
            early_vblank_flushes++;
            if(!GET_VDP_STATUS(VDP_VBLANK_FLAG))vblank_flush_overruns++;
        } else SYS_doVBlankProcess();
        last_presented=vtimer;
    }
    return 0;
}
