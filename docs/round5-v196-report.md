# Round 5 v1.9.6 hardware report — 2026-11-02

Diego Attomic reports a mid-stage crash and missing secret-wall items on a
Mega Drive 3 with an “EverDrive X7 ultra instant save”. The exact board,
cartridge/firmware identity, wall location, and whether a save state was
loaded are unknown. The supplied photo does show an exception screen.
Source: https://rester159.itch.io/black-tiger-md (November 2 comment).

## Binary identification and crash screen

The archived published ROM is `dist/blacktiger_MD_v1.9.6.bin`, SHA-256
`b53aea19996347237ff892c9a994a96c5951dd8d523a2a56904a3ccf101972a3`.
Analysis uses its matching `dist/blacktiger_MD_v1.9.6-symbols.txt`, not the current Credits build.
The reporter's own file hash is unknown, but the displayed addresses match
this archive's error-handler layout.

- `0x051A6A` lies in the inline “ILLEGAL INSTRUCTION” message following
  `MDDBG__IllegalInstr` at `0x051A62`.
- Stack entries repeatedly show SR `2700` and PC `00051A6A`.
- `0x050D60` is the error handler's VDP-setup return instruction; `0x050AEC`
  is the instruction after that routine's call.
- `0x042CF2` is the expected empty H-interrupt callback.

These entries point to faults occurring inside the error handler and do not
identify the original gameplay instruction. They do not establish a stack
overflow, faulty cartridge, or save-state incompatibility. A synthetic
illegal instruction at RAM `0xFFFE00` on Genesis Plus GX with the exact release
ROM correctly displays that injected address, without reproducing the nested
faults in the photo (`reports/v196-exception-probe.png`). This tests the
handler under that emulator only; it does not reproduce the reported crash.

## Secret-wall findings

Reading the original arcade ROM's Round 5 placement records directly gives:

| Persistent ID | Actor position | Reward |
|---|---|---|
| 41 | 1952, 232 | 5,000 points |
| 42 | 1968, 232 | None |
| 43 | 992, 296 | None |
| 44 | 992, 328 | Armor +2, capped at 8 |
| 45 | 1920, 584 | None |
| 46 | 1920, 616 | 500 Zenny |

The three no-reward walls use original constructor `02:B7DA`; they intentionally
have transparent reveal art. The other three rewards appear in the released
ROM's sprite table with nontransparent graphics. This is a possible explanation
of the comment, not confirmation of which wall the reporter meant.

Validation performed:

- Fresh execution of the original arcade routines in MAME: 39 terrain patches
  and 12 reward types pass (`reports/hidden-oracle.json`).
- Published ROM, matching symbols, Genesis Plus GX: all 39 hidden-wall cases
  pass reveal, terrain, respawn and collection checks
  (`reports/hidden-v196-released-runtime-tests.json`).
- Current local Credits build: the same 39-case regression passes
  (`reports/hidden-runtime-tests.json`).
- Published ROM: all six Round 5 walls pass SAT/pixel checks against their
  reward type; original placement bytes independently match native placements
  (`reports/round5-released-wall-visual-tests.json`).

The wall fixtures inject nearby positions and projectiles; they do not prove
natural traversal or crowded-scene rendering. Reproduce the focused released
ROM check with `.venv/bin/python tools/check_round5_report.py`. It pins both
ROM and symbol hashes. Screenshots are `reports/v196-round5-wall-41.png`
through `reports/v196-round5-wall-46.png`.

## Disposition

No gameplay fix is justified by the reproduced evidence. Preserve the three
arcade-empty walls. The hardware crash remains unresolved; a precise route,
affected wall image, or reproducible save state and exact ROM/cart identity
would enable a targeted follow-up. The user has no further details or hardware
access. No ROM was changed, released, or uploaded for this report, and no
comment was posted.
