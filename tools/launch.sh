#!/bin/sh
# Per-launch settings: leave the user's global RetroArch configuration intact.
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
core_path="$HOME/Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib"
exec open -n -a RetroArch --args --appendconfig "$project_dir/tools/retroarch.cfg" -L "$core_path" "$project_dir/dist/blacktiger_astra.bin"
