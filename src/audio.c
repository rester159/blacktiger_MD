#include "game.h"
#include "music.h"
#include <genesis.h>
/* Native FM stream player plus provisional PSG effects. */
static u8 audio_ready,pal_audio,high_frequency[2],last_audio_mode=255;
static u32 audio_video_frame;
void music_write(u8 part,u8 reg,u8 value) {
    if(pal_audio && reg>=0xa4 && reg<=0xa6){high_frequency[part]=value;return;}
    if(pal_audio && reg>=0xa0 && reg<=0xa2){
        u16 f=(((u16)high_frequency[part]&7)<<8)|value;
        f=((u32)f*33070+16384)>>15;
        YM2612_writeReg(part,reg+4,(high_frequency[part]&0x38)|(f>>8));
        value=f;
    }
    YM2612_writeReg(part,reg,value);
}
static void music_update(void) {
    u32 now=vtimer;u16 elapsed=now-audio_video_frame;u8 bus,mode=game.mode;
    audio_video_frame=now;
    bus=Z80_getAndRequestBus(TRUE);
    if(!audio_ready){YM2612_reset();audio_ready=1;pal_audio=SYS_isPAL();elapsed=0;}
    if(mode==TITLE) {
        music_request=0;if(music_active)music_stop();
    } else {
        u8 request=music_request;music_request=0;
        if(mode!=last_audio_mode) {
            if(mode==SHOP)request=0x2c;
            else if(mode==CLEAR)request=game.round==7?0x33:0x32;
            else if(mode==GAMEOVER)request=0x31;
            else if(mode==ENDING && music_command!=0x33)request=0x33;
            else if(mode==PLAY && !request && (last_audio_mode==DEAD || last_audio_mode==SHOP ||
                    last_audio_mode==TITLE || music_round!=game.round))request=0x21+game.round;
        }
        if(request)music_start_command(request);else music_advance(elapsed,pal_audio);
    }
    last_audio_mode=mode;
    if(!bus)Z80_releaseBus();
}
void audio_tick(void) {
    static u8 age, sound;
    music_update();
    if (game.sound) {
        sound = game.sound;
        age = 18;
        PSG_setEnvelope(0, 0);
        PSG_setEnvelope(3, 15);
    }
    if (age) {
        u16 period;
        age--;
        switch (sound) {
        case SND_ATTACK:
            period = 180 + age * 8;
            break;
        case SND_JUMP:
            period = 80 + age * 16;
            break;
        case SND_COIN:
        case SND_BUY:
        case SND_RESCUE:
            period = age > 9 ? 180 : 120;
            break;
        case SND_CLEAR:
            period = age > 12 ? 240 : age > 6 ? 190 : 160;
            break;
        default:
            period = 500 + age * 16;
            break;
        }
        PSG_setTone(0, period);
        PSG_setEnvelope(0, (18 - age) >> 1);
    } else
        PSG_setEnvelope(0, 15);
}
