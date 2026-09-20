#include "game.h"
#include <genesis.h>
volatile u16 frame_cost[3];
int main(bool hardReset) {
    u16 pal_phase = 0;
    (void)hardReset;
    JOY_init();
    video_init();
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
        if (joy & BUTTON_C)
            in |= IN_MAGIC;
        if (joy & BUTTON_START)
            in |= IN_START;
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
        SYS_doVBlankProcess();
    }
    return 0;
}
