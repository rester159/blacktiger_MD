#!/usr/bin/env python3
"""Generate all build assets locally from a validated original ROM set."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from arcade_source import ROOT, Source

GENERATORS = ('extract.py', 'build_ui.py', 'build_intro.py', 'build_hud.py',
              'build_shop.py', 'build_attract.py', 'build_arena_parallax.py', 'build_backdrops.py',
              'pack_sprite_atlas.py', 'build_cave_geometry.py')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    source = Source()
    subprocess.run([sys.executable, str(ROOT/'tools/prepare_source_data.py')], cwd=ROOT, check=True)
    inputs = sorted(set((ROOT/'tools').glob('*.py')) | set((ROOT/'tools').glob('*.lua')))
    inputs += [ROOT/'assets/board.json', ROOT/'assets/rom_manifest.json',
               ROOT/'art/black_tiger_md_logo_concept.png', ROOT/'art/yashichi.png',
               ROOT/'reference/.source-data.json']
    signature = hashlib.sha256(''.join(digest(p) for p in inputs).encode()).hexdigest()
    stamp = ROOT/'.local/assets-build.json'
    old = json.loads(stamp.read_text()) if stamp.exists() else {}
    if old.get('signature') == signature and old.get('outputs') and all((ROOT/p).is_file() and digest(ROOT/p)==h for p,h in old['outputs'].items()):
        print('Local generated assets are current; original ROM verified.')
        return
    for generator in GENERATORS:
        print(f'Generating: {generator}', flush=True)
        subprocess.run([sys.executable, str(ROOT/'tools'/generator)], cwd=ROOT, check=True)
    outputs = list((ROOT/'src').glob('*.inc')) + list((ROOT/'res/generated').glob('*'))
    outputs += [ROOT/'src/data.c', ROOT/'src/actor_dispatch.c', ROOT/'inc/assets.h', ROOT/'res/assets.res']
    stamp.parent.mkdir(exist_ok=True)
    stamp.write_text(json.dumps(dict(signature=signature, source_set=source.lock['aggregate_sha256'], outputs={str(p.relative_to(ROOT)):digest(p) for p in outputs if p.is_file()}),indent=2)+'\n')

if __name__ == '__main__':
    try:
        main()
    except (ValueError,OSError,RuntimeError) as error:
        sys.exit(str(error))
