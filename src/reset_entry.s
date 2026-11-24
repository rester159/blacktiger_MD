* Reset button entry: the Makefile links with --wrap=_reset_entry, so sega.s
* (and SYS_reset) arrive here instead of SGDK's partial warm start.
*
* SGDK's warm start keeps work RAM, skips the TMSS unlock and runs its whole
* hardware init once before main() can ask for a cold start. Running that init
* a second time, with the Z80 already released, is what froze a Mega Sg. Put
* the hardware back to its power-on state and take the single cold start.
*
* Entered with interrupts masked, both stacks set and the Z80 bus requested.

.section .text

    .globl  __wrap__reset_entry

__wrap__reset_entry:
    move.w  #0x2700,%sr

* Full Z80 and YM2612 reset while the 68000 keeps the Z80 bus.
    move.w  #0x0100,0xA11100
    move.w  #0x0000,0xA11200
    moveq   #63,%d0             /* well over the YM2612's 192-cycle minimum */
1:  dbra    %d0,1b
    move.w  #0x0100,0xA11200

* Controller ports back to their power-on direction and value.
    moveq   #0,%d0
    lea     0xA10003,%a0
    move.b  %d0,(%a0)           /* data 1, 2 and EXT */
    move.b  %d0,2(%a0)
    move.b  %d0,4(%a0)
    move.b  %d0,6(%a0)          /* control 1, 2 and EXT */
    move.b  %d0,8(%a0)
    move.b  %d0,10(%a0)

* TMSS unlock: sega.s only does this on its cold path.
    move.b  0xA10001,%d0
    andi.b  #0x0F,%d0
    beq.s   2f
    move.l  #0x53454741,0xA14000

* Save RAM unmapped and ROM banks linear before ROM data is copied.
2:  lea     0xA130F1,%a0
    moveq   #0,%d0
    moveq   #7,%d1
3:  move.b  %d0,(%a0)
    addq.l  #2,%a0
    addq.b  #1,%d0
    dbra    %d1,3b

    jmp     _start_entry
