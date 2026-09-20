#include "progress.h"
#include "assets.h"
volatile u8 progress_max_hp;
void progress_new(void) {progress_max_hp=progress_initial_health;}
void progress_score(u16 points) {
 u8 maximum=progress_max_hp;
 game.score=(game.score+points)%100000000UL;
 /* The original score task advances one threshold per award, without healing. */
 if(maximum>=1 && maximum<=4 && game.score>=progress_thresholds[maximum-1])progress_max_hp=maximum+1;
}
