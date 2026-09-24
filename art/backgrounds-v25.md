# Existing-art parallax cleanup, v25

Only the existing game artwork is used. There are no generated illustrations or new palette styling in the cartridge. The original eight scenery palettes, foreground contours, collision maps, actor palettes and HUD glyphs are retained.

`tools/build_backdrops.py` reconstructs the parallax motifs from `scenery*.npy`, the indexed original level artwork emitted by the arcade asset extractor:

- Level 4 retains the original mirrored cave-rock texture.
- Level 5 takes the original blue ridge at world rectangle (640, 784, 176, 112), removes non-mountain pens containing an arrow marker, and mirrors the clean half. This excludes the wall and column fragments imported by the previous wide crop.
- Level 6 takes the original temple at (1648, 16, 96, 64) and the original distant rock at (512, 256, 64, 32). Repeating the rock's middle tile pair gives the temple a matching 96-pixel footing. Two more original rock motifs occupy the open sky. No foreground platform or rectangular mist fragment is imported into the far plane.
- Level 7 retains the original stained glass. A reflected upper cap completes the lower silhouette, and the entire window is inset from the parallax plane's boundary.
- Level 8 retains its original palace/window composition and mirrored source landscape, with stray gold foreground fragments trimmed from the distant crop.
- Levels 1–3 retain their original masonry and backgrounds.

The cleaned motifs compile into native 8 × 8 tiles using the existing level palettes. Outer sky margins match for horizontal/vertical repetition; no image is painted across the screen during gameplay. Opaque level 5/6 HUD backgrounds are removed.

See `reports/backgrounds-all-eight-v25.png` for the eight native background previews and `reports/background-art-runtime-tests.json` for palette, scrolling/cache and seam checks. Each preview is one sampled view, with actors and HUD hidden by the capture fixture, not a complete map.
