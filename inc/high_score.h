#ifndef HIGH_SCORE_H
#define HIGH_SCORE_H
#include "game.h"
#define HIGH_SCORE_COUNT 5
typedef struct {u32 score;char initials[3];u8 mode;} HighScoreEntry;
extern u32 high_score;
extern HighScoreEntry high_scores[HIGH_SCORE_COUNT];
extern u8 high_score_pending,high_score_cursor;
void high_score_init(void);
void high_score_save(void);
void high_score_begin(void);
void high_score_finish(void);
void high_score_letter(u8 up);
void high_score_confirm(void);
#endif
