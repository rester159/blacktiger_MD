# Alternate-area transition audit

The native asset extractor skips fixed constructor 6F71. Its 12 rows are the
entrance and exit triggers in rounds 1–6, not decorative hidden pickups. Rounds
7–8 have no such rows. `bonus.json` extracts every row, preserving its original
persistence key, plus the eight destination camera pairs and return adjustments.

Constructor 6F7D copies the invisible 32-byte template at 6FAE. Its contact
category is 22, dispatched through fixed4795 to 4F8C, with half extents 6×6.
Contact is rejected while F412 (jumping), F418 (falling), or F416 (camera return)
is nonzero. Accepted contact clears the attack-active byte, sets actor contact
mask 0B, marks the source row consumed (OR 2), and starts 6FD7.

The transition clears F440–FDFF and active occupancy counts, clears poison
state F424/F425, and clears only bit 0 of each persistent source row. Consumed
bits therefore survive. Entry saves the logical camera in E038/E03A; the X
adjustment from 7130 is an 8-bit addition to the low world-coordinate byte,
with no carry into the high byte. Destination pairs at 7110 are little-endian
pixel coordinates, copied into big-endian camera storage. Exit restores the
saved camera. Entry requests music 2D; exit requests round+21.

F3B7 is a **has-entered latch**, not a flag that toggles on every door: it stays
set on exit and resets in the life/round initialization paths at 1ECE/1F09.
Both source triggers are one-shot until the relevant persistence reset.

The background task selects the table at 2B00 or 2B10 using that latch. Each
round has eight update lists in bank4: two animation phases, each split across
four background RAM banks. Each list writes (destination address, tile word)
pairs. `bonus.json` retains all source tile words and flattened map offsets.
The task applies one RAM-bank list per update and waits ten task ticks between
phases. These changes include doorway artwork; implementation must compile
both phases into native map tiles and collision values with the established
palette mapping. Do not merely teleport into the static extracted map.

`bonus_oracle.lua` executes the original contact gate and camera-selection
instructions. It skips task scheduling and audio calls at explicit callsites;
it does not claim to verify their behavior, transition presentation, background
writes, or native integration. The runner checks original outputs against the
extracted coordinate policy, including low-byte overflow and nonzero movement
flags. The captured traces are development evidence only; original program
instructions must never enter the cartridge.

Remaining integration: native trigger state and collision; shared transient-pool
reset preserving player rewards and consumed rows; player/camera relocation;
door/background animation and collision patches; transition presentation;
death/restart behavior and natural entrance-to-exit cartridge validation.
