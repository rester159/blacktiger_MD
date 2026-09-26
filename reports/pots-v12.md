# v1.2 pot restoration

Restored 251 arcade pot placements across all eight levels, the original
32-entry/16-swap contents algorithm, two-hit breakage, source animation frames,
Zenny/key/time rewards, four enemy traps, and persistent opened/collected state.
The level-3 vertical wrap and level-7 shared pot ID are covered by cartridge tests.

Validation: all 172 Makefile test commands passed on the final cartridge.
This includes 128 original-Z80 shuffle comparisons, visits to all 251 positions,
actual attack input, all item/trap variants and checkpoint persistence. Strict
packaging also passed the current-ROM all-level performance, runtime profiling,
and 48 pinned sprite-render fixtures. The existing busy-encounter thresholds
remain unchanged and pass after reducing pot scanning overhead.

The source-only repository remains ROM-dependent. Generated assets, observations,
and cartridges remain ignored. See `reference/pots.md` for source addresses and
scope, including native pool limits and global RNG scheduling differences.

Initially saved over the local v1.2 and compatibility v1 filenames; subsequently
reissued as v1.3 at the user's request.
Full-rate rendering in every busy scene and real-hardware/PAL validation are
not claimed.

Tested v1.2 4 MiB cartridge SHA-256: `5c75c5d0c746162a864bb77d37fd620e37ea354772a9950657fe996045df8bf8`.

## v1.3 version update

The Home/title corner label now reads v1.3. A complete cartridge byte comparison
confirmed exactly five changed bytes, confined to the version glyph and ROM
checksum. The arcade UI/coin test was rerun on v1.3 and the rendered label was
visually checked. The 172-test run above applies to the otherwise identical
v1.2 gameplay build, rather than being represented as a new full-suite run.

v1.3 SHA-256: `d4182ae84ea43afa4854c6924a22b8d572aa936ad75ac3d1ef9182405471b989`.
