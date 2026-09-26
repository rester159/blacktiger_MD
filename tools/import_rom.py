#!/usr/bin/env python3
"""Import an owner-supplied Black Tiger set; never download ROM files."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'assets/rom_manifest.json'

def read_set(path):
    manifest = json.loads(MANIFEST.read_text())
    result = {}
    archive = zipfile.ZipFile(path) if path.is_file() else None
    try:
        for row in manifest['files']:
            name = row['path']
            if archive:
                matches = [n for n in archive.namelist() if Path(n).name == name]
                if len(matches) != 1:
                    raise ValueError(f'Expected exactly one {name} in {path}')
                raw = archive.read(matches[0])
            else:
                candidate = path / name
                if not candidate.is_file():
                    candidate = path / 'payload' / name
                if not candidate.is_file():
                    raise ValueError(f'Missing {name} in {path}')
                raw = candidate.read_bytes()
            if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError(f'Wrong ROM revision or damaged file: {name}; see assets/rom_manifest.json')
            result[name] = raw
    finally:
        if archive:
            archive.close()
    return manifest, result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path, help='ZIP, extracted ROM directory, or existing source package')
    parser.add_argument('--destination', type=Path, default=ROOT/'assets/source/arcade')
    args = parser.parse_args()
    try:
        manifest, files = read_set(args.rom)
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        parser.exit(1, f'ROM import failed: {error}\n')
    # Validate the entire set before touching an existing local package.
    args.destination.mkdir(parents=True, exist_ok=True)
    (args.destination/'payload').mkdir(exist_ok=True)
    for name, raw in files.items():
        (args.destination/'payload'/name).write_bytes(raw)
    (args.destination/'source_lock.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Validated and imported {len(files)} ROM files into {args.destination}')

if __name__ == '__main__':
    main()
