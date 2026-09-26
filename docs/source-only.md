# Source-only repository

Tracked inputs are native port code, offline converters/oracle scripts, tests, documentation, board layout metadata, the ROM hash manifest, and the port's custom Home-menu artwork. Original graphics, audio, maps, actor templates, and observed presentation/music events are rebuilt locally from the supplied ROM.

Ignored local outputs include:

- `assets/source/`, `assets/ui/`, `res/generated/`;
- generated `src/*.inc`, `src/data.c`, `src/actor_dispatch.c`, `inc/assets.h`, and resource declarations;
- `reference/` observation data and `reports/` data/media (Markdown documentation remains tracked);
- `out/`, `dist/`, `screenshots/`, `.venv/`, and `.local/`.

A normal build validates all ROM hashes before compiling, including incremental builds with cached assets. `tools/import_rom.py` supports ZIP and extracted inputs and validates everything before changing a local package. No ROM download service or bundled payload is provided.

The current tree and published Git history have been rewritten to remove ROMs, compiled cartridges, extracted/generated assets, raw observation dumps, screenshots and borrowed boot data. The historical audit removed 661 paths across 107 commits while preserving the current source tree. No GitHub release attachments were present.

Old clones, forks, cached downloads and server-retained unreachable objects are outside the rewritten branch history. GitHub may retain cached commit views or orphaned LFS objects; the force-push does not prove physical deletion from GitHub storage. Re-clone after this rewrite; do not merge an old clone back into the cleaned repository.

The local migration backup is under `.local/source-only-backup/`. It includes the previous working files and index, `pre-history-rewrite.bundle`, and `pre-history-lfs/`; the original local ROM and compiled v1.2 remain outside the tracked source tree. The source-only startup omits assets copied from Sonic, Shinobi and Street Fighter II. Black Tiger's own title, story intro, music and gameplay are still generated from its ROM.

## Migration validation

A fresh export containing only the source-only Git files compiled successfully using the supplied ROM package, MAME 0.288, and the local SGDK/Python toolchain. It started without any generated assets or observation dumps. All 97 regenerated game-data files matched the previous v1.2 files byte-for-byte. The source-only cartridge SHA-256 was `7f3a41dfed6ba02a8c4e3c8e2bb4dd2ead2011ca40b372e21ae16d6ff3c561a8`.

Both fresh and cached builds refused missing ROMs. ZIP/extracted import, corrupt-ROM rejection, authoritative manifest checks, and failed-import preservation passed. Runtime checks passed for the new startup and held Start, original Black Tiger intro, controls, Arcade coins, menu/shop/poison presentation, dragon colors, opening wall, level 2 respawn, boss bars and torches. The full historical release suite was not rerun for this repository conversion.

Run `python3 tools/check_source_tree.py` to check the current Git index for accidentally reintroduced payloads or generated files. This audit does not inspect history.
