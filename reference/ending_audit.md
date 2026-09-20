# Native ending contract

`tools/ending_oracle.lua` executes fixed 7B98 through the jump to 2013 in the
supplied original ROM. It records 560 character writes, twelve clear requests,
ten observed palette states, a layer-hide event, the credits backdrop, and every
0116 scheduler wait. The six opening palette steps each last 60 task updates;
characters wait 2, new lines 30, pages 120, and the terminal hold 180. The captured
sequence reaches 2013 at update 4514. The four one-update palette-loader yields
before the credits map are included.

The oracle initializes inherited global/round-eight palettes from original copy
lists. It bypasses actor-task deletion and directly services queued character
clears over D080–D3BF; it does not run the complete arcade board scheduler.
Those choices are recorded in the report. The layer-hide instruction is witnessed
at 7C6E, and the capture preserves its AF effect when continuing after that marker.
The final source branch at 20C7–20CC excludes a completed eighth round from the
ordinary continue offer.

`tools/extract_ending.py` compiles typed character, clear, palette, scene and end
events. Original CPU instructions are not shipped or interpreted. The native
`ending.c` sequencer owns its update counter, text cells and dirty-row mask.
The source character layout, spelling and punctuation are preserved. Six opening
terrain palette steps are adapted through the existing round-eight palette
mapping: each Genesis pen uses the pixel-frequency-weighted mean of its contributing
source colors. This is a documented color approximation. The credits backdrop and
lettering retain all their RGB333 colors.

The ending font uses 31 previously unused VRAM tiles at 1408, so the last victory
sprites and terrain remain intact during the story. Only dirty character rows
are uploaded. At the source hide/credits transition the renderer removes sprites,
installs the final map and changes palettes. The ordinary console HUD remains;
original HUD and whole-board verification of retained victory sprites are open.

After the terminal event, the native game-over notice runs once, skips the
continue offer, and returns to the title. Start does not interrupt the ending.
The original high-score/name-entry path remains unimplemented. A new game resets
ending state and restores terrain/graphics caches.

Validation:

- `tests/test_ending.py` compiles production C and compares all 4515 observed
  states, all characters, dirty rows, palette/scene changes and completion.
- `tests/test_ending_runtime.py` enters through an injected final victory and
  traverses all pages, checking actual map/pattern/palette VRAM in stable source
  waits, music continuity, repeated Start inputs, terminal game over, suppressed
  continue, and new-game terrain restoration. Captured story and credits screens
  were visually inspected.

These are subsystem and lifecycle checks, not a natural eight-round playthrough,
arcade-wide scheduler comparison, PAL/hardware validation, or proof that every
presentation detail is complete.
