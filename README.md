# Black Tiger MD — source-only v1.5

Arcade now opens into the original ranking/title/demo sequence. Its Top 5 and title header display SRAM-backed records; demo playback cannot earn scores, overwrite initials, or spend credits. Press Start to insert a coin, A to start, Up/Down for DIP switches, and B to return to the mode selector. Arcade returns to attract after game over (and after confirming qualifying initials).

The attract presentation replays an observed original arcade cycle with native tiles and sprites, including the large logo over the gameplay demonstration. It preserves the captured frame sequence, scrolling and sprite positions; subsequent loops repeat that witnessed cycle. Mega Drive palette and sprite limits still apply. The cartridge does not execute the arcade CPU.

The title displays the live SRAM high score. Select HIGH SCORES below Arcade/Home to view five saved records; qualifying runs offer three-letter initials (Up/Down changes a letter, A advances or confirms, B returns to the previous letter). Records show Arcade, Home, or Boss Rush mode. Existing v1.4 high scores migrate automatically; interrupted saves can recover the previous record.

Enable battery/save RAM in your emulator. When moving from the v1.4 to v1.5 ROM filename, copy the old battery save to the new filename so the emulator loads it. Debug sessions do not enter the table.

US shop prices are weapons 100/1000/2400/9600, armor 80/300/800/1600, key 30, and antidote 150; combat difficulty does not change this catalog. Dialogue draws over overlapping world sprites.

Home Up/Down cycles through Play, Boss Rush, and Options. Ground acid blobs finish their death animation after a hit instead of returning as harmless moving ghosts.

A native Sega Mega Drive/Genesis port built with SGDK. The cartridge runs native 68000 game logic; it does not emulate the arcade CPU.

**You must supply the original Black Tiger arcade ROM set to build this project.** This checkout contains port code, conversion tools, and a filename/size/SHA-256 manifest. It does not include original ROMs, compiled cartridges, extracted graphics/music, generated C asset tables, screenshots, or original-ROM observation dumps.

## Build

Requirements:

- Python 3 with support for the versions in `requirements.txt`.
- SGDK with native `m68k-elf-gcc`, Make, and Java. The default SDK directory is `~/mars/m68k-elf`; override it with `GDK=/path/to/sgdk`.
- MAME with Lua/debugger support to generate the local source observations. Tested with MAME 0.288. Put `mame` on PATH or set `MAME=/absolute/path/to/mame`.
- The exact 20-file arcade set listed in [assets/rom_manifest.json](assets/rom_manifest.json). Other revisions are rejected rather than silently producing incorrect data.

```sh
python3 tools/import_rom.py /path/to/blktiger.zip
make
```

The importer also accepts an extracted ROM directory. It validates the complete set before writing anything. It never downloads ROMs.

`make` creates the Python environment, verifies the original ROM, runs the offline MAME observations, converts graphics/maps/animation/music to native data, and compiles `out/release/rom.bin`. The first build takes longer because all observations and assets are generated locally; subsequent builds reuse verified local outputs. ROM validation is required even when generated assets already exist.

For different tool locations:

```sh
MAME=/path/to/mame make GDK=/path/to/sgdk JAVA=/path/to/java
```

To use a previously imported ROM package outside this checkout:

```sh
BLACKTIGER_SOURCE=/path/to/package make
# package/payload/ contains the filenames listed in assets/rom_manifest.json
```

The repository's manifest remains authoritative; a package's own lock file cannot substitute a different revision. The offline tools execute the supplied arcade ROM only to derive local data. No arcade program is linked into the cartridge.

Open the locally built `out/release/rom.bin` in a Genesis emulator. The original Black Tiger story intro remains. The earlier Sonic/Shinobi/Street Fighter boot sequence is omitted so those additional games are not required or distributed.

## Controls

- D-pad: move, crouch, and climb.
- A: chain attack and dagger volley; release to attack again. B: jump.
- Arcade menu: Start inserts a coin; A selects and spends a credit to play or continue.
- Home: Start plays and pauses/resumes. Home also includes Boss Rush and options.
- Shop: D-pad selects; A buys; B exits.

## Development checks

```sh
make references    # Generate additional original-ROM test fixtures locally
make test          # Build, prepare those fixtures, then run the full release suite
```

Runtime checks also require a Genesis Plus GX libretro core with exported diagnostic symbols; set `BLACKTIGER_CORE` to its path. The developer's default is `.local/test-core/genesis_plus_gx_libretro.dylib`. The instruction profiler additionally requires its pinned ARM64 core. These emulator dependencies are not needed to compile the cartridge.

`python3 tools/package.py` is an optional local packaging step after the complete release suite passes. `dist/` is private build output and is ignored by Git. Do not add ROMs, release binaries, or generated data to the source repository.

See [docs/source-only.md](docs/source-only.md) for the tracked/generated boundary and Git-history limitation, and [docs/performance.md](docs/performance.md) for recorded gameplay performance work.
