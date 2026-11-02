# Undead emergence weapon timing — 2026-11-02

Confirmed against the owner-supplied arcade ROM and its recorded MAME traces.

The shared medium-actor weapon loop (fixed Z80 340C–3411) checks mode bit 0.
Player contact (3455–345A) checks bit 1 separately. Bank 0 callbacks 808F,
8418 and 8A55 set mode 0A for the three recurring undead variants: weapons
are allowed, player contact is disabled. Later callbacks set mode 08.
The port previously used the contact flag for both decisions.

For the basic undead, the trace reaches mode 0A on update 73, after three
24-tick animation frames. Two more 24-tick frames precede mode 08. The fix
restores this 48-update partially emerged damage window without enabling
premature body-contact damage. Hidden/receding/dead phases remain protected.

The new weapon-gate assertion fails on the old code at emerge_left update 73.
After the fix, all 16,660 recorded actor updates across the three family tests
match the source weapon and contact gates. Existing three-family runtime
regressions pass. The new 18-case linked-ROM regression passes on Genesis
Plus GX and PicoDrive, covering hidden, partial and full emergence with native
daggers and diagnostic full-strength shots. Positioning is injected; this is
not a complete controller-driven playthrough or physical-hardware test.

Local build SHA256: 867665c63362d2440eb72e07c564c8c3084bb99be03e3d0bd81220050bd7dd91.
The packaged v1.9.6 BIN remains unchanged. This fix is not published or packaged
as a new release, and the full release suite has not been rerun for this build.
