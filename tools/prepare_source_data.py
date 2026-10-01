#!/usr/bin/env python3
"""Rebuild private ROM observations required by the offline asset converter."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from arcade_source import Source, ROOT
from oracle_runner import mame_binary

BUILD_ORACLES = ('constructor', 'progress', 'shop', 'clear', 'clear_screen',
                 'ending', 'npc_sequence', 'hud', 'shop_screen', 'intro', 'title', 'attract')

def run(name, *arguments):
    script = ROOT/'tools'/f'run_{name}_oracle.py'
    print(f'Observing original ROM: {name} {" ".join(arguments)}', flush=True)
    subprocess.run([sys.executable, str(script), *arguments], cwd=ROOT, check=True)

def cached_dragon_oracle_is_valid(source):
    """Reuse the checked-in local Dragon trace instead of replaying 1M MAME ticks."""
    report_path = ROOT/'reference/dragon_oracle.json'
    events_path = ROOT/'reference/dragon_oracle_events.txt'
    lua_path = ROOT/'tools/dragon_oracle.lua'
    if not (report_path.is_file() and events_path.is_file()):
        return False
    report = json.loads(report_path.read_text())
    mame = Path(mame_binary())
    return (
        report.get('source_set') == source.lock['aggregate_sha256']
        and report.get('lua_sha256') == hashlib.sha256(lua_path.read_bytes()).hexdigest()
        and report.get('mame_sha256') == hashlib.sha256(mame.read_bytes()).hexdigest()
        and report.get('trace_sha256') == hashlib.sha256(events_path.read_bytes()).hexdigest()
    )

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true', help='Also generate source-oracle fixtures for the complete development test suite')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    source = Source()  # Required even when local generated assets are cached.
    (ROOT/'reference').mkdir(exist_ok=True)
    (ROOT/'reports').mkdir(exist_ok=True)
    marker = ROOT/'reference/.source-data.json'
    scripts = [ROOT/'tools'/f'run_{n}_oracle.py' for n in BUILD_ORACLES]
    scripts += list((ROOT/'tools').glob('*_oracle.lua'))
    scripts += [Path(__file__), ROOT/'tools/oracle_runner.py', ROOT/'tools/spawn_catalog.py', ROOT/'tools/run_music_oracle.py']
    signature = hashlib.sha256(b''.join(p.read_bytes() for p in sorted(set(scripts))) + source.lock['aggregate_sha256'].encode()).hexdigest()
    old = json.loads(marker.read_text()) if marker.exists() else {}
    valid = old.get('signature') == signature and all((ROOT/p).is_file() and hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in old.get('outputs',{}).items())
    if args.force or not valid:
        mame_binary()
        for name in BUILD_ORACLES:
            run(name)
        for command in range(0x20, 0x3a):
            if command != 0x38:
                run('music', hex(command))
        outputs = []
        for name in BUILD_ORACLES:
            if name == 'constructor':
                outputs += [ROOT/'reference/constructors.json', ROOT/'reference/constructor_oracle_events.txt']
            else:
                outputs += [ROOT/'reference'/f'{name}_oracle.json', ROOT/'reference'/f'{name}_oracle_events.txt{ ".gz" if name == "intro" else "" }']
        outputs += list((ROOT/'reference/music').glob('*.json')) + list((ROOT/'reference/music').glob('*.txt'))
        outputs.append(ROOT/'assets/ui/title_arcade.png')
        outputs.append(ROOT/'reference/attract_oracle_frames.bin.gz')
        marker.write_text(json.dumps(dict(signature=signature, outputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}),indent=2)+'\n')
    if args.all:
        # Build data must already have been converted for behavior fixture runners.
        if not (ROOT/'reports/assets.json').exists():
            parser.error('Run make first, then make references or make test.')
        for script in sorted((ROOT/'tools').glob('run_*_oracle.py')):
            name = script.stem.removeprefix('run_').removesuffix('_oracle')
            if name not in BUILD_ORACLES and name != 'music':
                if name == 'dragon' and cached_dragon_oracle_is_valid(source):
                    print('Reusing verified original-ROM observation: dragon', flush=True)
                    continue
                run(name)
    print('Original-ROM observations ready.', flush=True)

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError) as error:
        sys.exit(str(error))
