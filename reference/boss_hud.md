# Original arcade boss HUD

Source set: `assets/source/arcade/source_lock.json` (the supplied Black Tiger ROM set).

The original fixed routine `5D6D` reads remaining health **layers** from actor offset `15`. The drawing routine `5D88` writes two character cells per layer at `D0C7`, visible tile column 7, row 4. Filled cells are `80/81`; depleted cells are `82/83`. Attribute bit 5 selects the second character bank. Depleted cells retain the source outline and transparent center; the original routine does not replace them with dashes or erase the outline.

| Stage | Segments | Character attribute | Source fill RGB444 |
|---|---:|---|---|
| 1 | 2 | 29 | D00 (red) |
| 2 | 2 | 29 | D00 (red) |
| 3 | 3 | 29 | D00 (red) |
| 4 | 3 | 29 | D00 (red) |
| 5 | 5 | 29 | D00 (red) |
| 6 | 6 | 2A | D70 (amber) |
| 7 | 6 | 2A | D70 (amber) |
| 8 | 8 | 2A | D70 (amber) |

This table comes from fixed ROM `5DB6`; the observed character palette comes from `reference/hud_oracle_events.txt`. This supplied ROM does **not** use a universal yellow → red threshold based on percentage HP. Genesis glyphs use the nearest stable available actor-palette colors, so RGB values remain a hardware palette adaptation rather than an exact RGB444 match.

The row changes at layer depletion, through original callbacks bank 4 `A0B0` (stone body), bank 3 `9715` (dragons), bank 1 `9AAB` (wave bosses), and bank 1 `A11D` (hunter boss). Partial-damage routines update actor HP without calling the HUD renderer. Pending hit animation likewise does not deplete the row until the layer callback runs. The final callback renders zero filled cells, retaining empty outlines through defeat; encounter cleanup removes the row.

Original boss-entry routine `59BF` also clears the Zenny icon/count cells (columns 24–30, visible rows 3–4). The native HUD now reproduces this and restores currency afterward. Boss Rush selects its roster stage, not the shared palace-map index. Upper stone pieces do not control the bar.

`tools/run_boss_hud_oracle.py` invokes the original routine in MAME for all 43 valid stage/layer combinations. `tests/test_boss_hud_runtime.py` compares actual Genesis VRAM against those source character writes in regular and Boss Rush contexts, verifies partial-hit stability, color mapping, empty defeat outlines and cleanup. These are controlled fixtures, not a natural playthrough.
