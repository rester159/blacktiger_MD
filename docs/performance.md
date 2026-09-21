# Rendering optimization results

Measured with Genesis Plus GX in 17 deterministic NTSC samples. Each sample spans 600 video frames (approximately ten seconds). Update counts include intervening game modes, so these are comparative load samples, not continuous-play FPS guarantees. No natural full playthrough or hardware validation is claimed.

| Scene | Before updates | After updates |
| --- | ---: | ---: |
| level1_entry | 592 | 590 |
| level2_entry | 594 | 596 |
| level3_entry | 528 | 533 |
| level4_entry | 548 | 559 |
| level5_entry | 589 | 587 |
| level6_entry | 487 | 487 |
| level7_entry | 545 | 545 |
| level8_entry | 570 | 573 |
| cave_middle | 420 | 467 |
| sky_middle | 474 | 539 |
| windows_middle | 470 | 472 |
| palace_upper | 331 | 453 |
| palace_lower | 436 | 521 |
| palace_blue | 594 | 594 |
| rush1 | 588 | 594 |
| rush5 | 576 | 598 |
| rush8 | 343 | 589 |

Shared changes apply to every level: losslessly repacked actor graphics, fewer DMA requests for 32×32 bodies, unrolled sprite scanline-budget checks, and a bounded 2 KiB late-VBlank submission window. Large bosses use one 32×32 hardware sprite per four original cells. Cave HUD scenery caches its geometry, and palace columns share a single conservative capacity check. Actor artwork, palettes, movement and AI are unchanged.

Level 8 windows and exposed blue scenery now share a resident half-speed landscape. Foreground columns retain their separate speed. The pixel test checks a 16-pixel camera move produces 8-pixel scenery motion.

All 17 samples recorded zero terrain-cache faults and zero VBlank overruns. The full regression suite passed. Additional tests compare five large-boss profiles in both facings against canonical source-cell geometry and actual VRAM pixels.

Some scenes remain below 60 updates per second, especially crowded Level 3/4/6/7 sections and the upper palace. Near-full-rate entry scenes show little change, and small differences of a few updates should not be treated as meaningful gains.

Reproduce with `make test`, then `.venv/bin/python tools/package.py`. `tools/profile_all_levels.py` accepts `--rom`, `--symbols`, and `--output` for comparison against an older matching ROM/symbol pair.
