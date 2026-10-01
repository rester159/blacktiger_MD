#include "game.h"
#include "frontend.h"
#include "attract.h"
#include "high_score.h"
#include "boot_logos.h"
#include <genesis.h>
volatile u16 late_vblank_debug[4];
/* Sample expensive SGDK diagnostic clocks once per sixteen presentations. */
u8 profile_frame;
volatile u16 profile_samples;
volatile u16 frame_cost[3], early_vblank_flushes, vblank_flush_overruns;
/* Diagnostic totals: catch-up ticks are full fixed simulation steps, never
   larger movement deltas. Discards only bound exceptional stalls. */
volatile u32 pacing_catchup_ticks, pacing_discarded_ticks;
volatile u32 pacing_presentations, pacing_prepared_ticks, pacing_async_presentations;
extern volatile u16 video_reload_count;
static volatile u8 presentation_pending;
static volatile u32 async_presented;
static volatile u16 graphics_end_line;
static volatile u8 graphics_overrun;
static void graphics_complete(void) {
    /* SGDK calls this after DMA/scroll/palette, before controller polling.
       Controller polling may finish in active display; VDP writes may not. */
    graphics_overrun=!GET_VDP_STATUS(VDP_VBLANK_FLAG);
    graphics_end_line=GET_VCOUNTER;
}
static void present_ready(void) {
    if(!presentation_pending)return;
    u16 line=GET_VCOUNTER,queued=DMA_getQueueTransferSize(),operations=DMA_getQueueSize();
    SYS_doVBlankProcessEx(IMMEDIATELY);
    async_presented=vtimer;
    pacing_presentations++;
    pacing_async_presentations++;
    if(graphics_overrun){vblank_flush_overruns++;late_vblank_debug[0]=line;late_vblank_debug[1]=queued;late_vblank_debug[2]=operations;late_vblank_debug[3]=graphics_end_line;}
    presentation_pending=0;
}
int main(bool hardReset) {
    u16 pal_phase = 0, prepared = 0;
    u32 last_presented=0xffffffff;
    u32 logic_video_frame;
    u8 previous_mode, previous_round;
    (void)hardReset;
    JOY_init();
    boot_logos();
    video_init();
    frontend_init();
    game_new();
    game.mode = TITLE;
    video_round();
    high_score_init();
    logic_video_frame=vtimer-1;
    previous_mode=game.mode;
    previous_round=game.round;
    SYS_setVBlankCallback(graphics_complete);
    SYS_setVIntCallback(present_ready);
    while (TRUE) {
        u32 now=vtimer;
        u16 elapsed=now-logic_video_frame, ticks=1, reload=video_reload_count;
        u8 mode=game.mode, round=game.round;
        logic_video_frame=now;
        /* A late presentation must not slow the world clock. Catch up at most
           two missed refreshes before drawing, preserving every collision/AI
           step. Menus and scene transitions never inherit gameplay debt. */
        if((mode==PLAY && previous_mode==PLAY && round==previous_round) ||
           (attract_active() && previous_mode==TITLE)) {
            /* A source title/demo transition can replace both planes. Keep
               its timeline debt so the replay catches up without losing ticks. */
            u16 limit=attract_active()?120:6;
            if(elapsed>limit){pacing_discarded_ticks+=elapsed-limit;elapsed=limit;}
            ticks=elapsed>3?3:elapsed?elapsed:1;
            /* Keep a small remaining debt for the next iteration. A single
               four-refresh spike must not permanently lose a world tick. */
            if(elapsed>ticks)logic_video_frame=now-(elapsed-ticks);
        }
        /* One tick may already have run behind the submitted frame. It
           belongs to this elapsed interval, never to an extra world step. */
        if(prepared){if(ticks>=prepared)ticks-=prepared;else ticks=0;prepared=0;}
        if(SYS_isPAL()) {
            pal_phase+=ticks;
            ticks+=pal_phase/5;
            pal_phase%=5;
        }
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
        profile_frame=!(pacing_presentations&15);
        u32 t0 = profile_frame?getSubTick():0;
        u8 sound=0;
        while(ticks--) {
            game_tick(in);
            /* Native sound_commands accumulate until audio_tick. Preserve
               the last legacy cue too, across a silent catch-up tick. */
            if(game.sound)sound=game.sound;
            if(game.mode!=mode || game.round!=round || video_reload_count!=reload)break;
            if(ticks)pacing_catchup_ticks++;
        }
        game.sound=sound;
        if(profile_frame){u32 now=getSubTick();frame_cost[0]=now-t0;t0=now;}
        video_frame();
        if(profile_frame){u32 now=getSubTick();frame_cost[1]=now-t0;t0=now;}
        if(game.mode!=mode || game.round!=round || video_reload_count!=reload)
            logic_video_frame=vtimer;
        previous_mode=game.mode;
        previous_round=game.round;
        /* Use the remaining blank only when both transfer volume and setup
           work fit. H32 budgeting uses 160 bytes/line, 32 bytes per DMA setup
           and a 2304-byte margin for scroll/joy processing. For the repeated
           NTSC counter range, 256-line is the smaller remaining interval. */
        u16 queued=DMA_getQueueTransferSize(),operations=DMA_getQueueSize();
        u16 line=GET_VCOUNTER;
        if(!SYS_isPAL() && vtimer!=last_presented &&
           GET_VDP_STATUS(VDP_VBLANK_FLAG) && line>=224 &&
           queued+operations*32+2304 <= (256-line)*160) {
            SYS_doVBlankProcessEx(ON_VBLANK);
            early_vblank_flushes++;
            if(graphics_overrun){vblank_flush_overruns++;late_vblank_debug[0]=line;late_vblank_debug[1]=queued;late_vblank_debug[2]=operations;late_vblank_debug[3]=graphics_end_line;}
        } else if(!SYS_isPAL() && game.mode==PLAY && mode==PLAY &&
                  game.round==round && video_reload_count==reload) {
            /* The completed DMA/SAT queue is immutable while logic prepares
               the following frame. Only the interrupt owns its submission. */
            u32 prep_start=profile_frame?getSubTick():0;
            __asm__ volatile("" ::: "memory");
            presentation_pending=1;
            if(vtimer!=logic_video_frame)pacing_catchup_ticks++;
            game_tick(in);
            pacing_prepared_ticks++;
            if(profile_frame)frame_cost[0]+=getSubTick()-prep_start;
            if(!game.sound)game.sound=sound;
            prepared=1;
            while(presentation_pending) __asm__ volatile("nop");
            __asm__ volatile("" ::: "memory");
            last_presented=async_presented;
        } else SYS_doVBlankProcess();
        if(!prepared){last_presented=vtimer;pacing_presentations++;}
        /* A variable FM register burst must not hold an already prepared
           graphics queue past its display deadline. Audio keeps its own
           refresh clock and consumes the same queued game events. */
        if(profile_frame)t0=getSubTick();
        audio_tick();
        high_score_save();
        if(profile_frame){frame_cost[2]=getSubTick()-t0;profile_samples++;}
    }
    return 0;
}
