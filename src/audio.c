#include "game.h"
#include <genesis.h>
/* Native PSG effects. Original YM2203 music is not yet arranged for YM2612. */
void audio_tick(void) {
    static u8 age, sound;
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
