"""A held diagonal jump at an arena edge must land, not restart every tick.

Inject only the initial approach position; source rows spawn their real boss.
All movement after that uses controller input. This is not a full level route.
"""
import hashlib
import json
from test_runtime import ROOT, Runner, state, put
from run_rom import CORE


def encounter(level, y_lap=0):
    r = Runner(ROOT / 'out/release/rom.bin')
    r.run(100)
    r.start_game(exploration=True)
    r.run(20)
    s = state(r)
    s.round, s.mode, s.mode_timer = level, 4, 0
    put(r, s)
    r.run(100)
    s = state(r)
    s.mode = 2
    put(r, s)
    r.run(30)
    s = state(r)
    x, y = (880, 1568 + y_lap) if level == 2 else (1300, 96)
    s.p.x, s.p.y = x * 256, y * 256
    s.p.vx = s.p.vy = 0
    s.p.invincible = 10000
    s.cam_x, s.cam_y = x - 112, (y - 144) & 65535
    put(r, s)
    r.run(30)
    s = state(r)
    s.mode = 1
    put(r, s)
    r.run(60)
    s = state(r)
    row = 79 if level == 2 else 65
    assert s.spawned[row] == 1 and any(a.active and a.source == row for a in s.actors), 'native boss did not spawn'
    return r, row


def run(case=None):
    checks = []
    cases = ((2, 0, 128), (2, 0, 64), (2, -2048, 128), (4, 0, 128), (4, 0, 64))
    for level, lap, direction in (cases if case is None else (cases[case],)):
        r, row = encounter(level, lap)
        try:
            # Reach the boundary on foot, then press and hold jump + up + direction.
            r.run(240, direction)
            s = state(r)
            floor = s.p.y // 256
            assert s.p.grounded, ('edge approach not grounded', level, floor)
            samples = []
            for frame in range(180):
                r.run(1, direction | 16 | 1)
                s = state(r)
                samples.append(s.p.y // 256)
            r.capture(f'boss-edge-round{level + 1}-{lap}-{direction}.png')
            assert 0 < floor - min(samples) <= 96, ('held jump relaunches at edge', level, lap, direction, floor, min(samples))
            assert s.p.grounded and len(set(samples[-20:])) == 1 and abs(s.p.y // 256 - floor) <= (16 if level == 4 else 0), ('jump did not land', level, lap, direction, floor, s.p.y//256, s.p.grounded, samples[-20:])
            assert s.mode == 1 and any(a.active and a.source == row for a in s.actors), ('encounter disappeared', level, lap, direction, s.mode, s.spawned[row])
            if level == 2:
                boss = next(a for a in s.actors if a.active and a.source == row)
                camera_y = (s.cam_y + 32768) % 65536 - 32768
                assert boss.x // 256 < s.cam_x + 256 and boss.x // 256 + 128 > s.cam_x, 'dragon outside horizontal view'
                assert boss.y // 256 < camera_y + 224 and boss.y // 256 + 64 > camera_y, 'dragon outside vertical view'
            checks.append(dict(round=level + 1, y_lap=lap, direction=direction, max_rise=floor-min(samples), landed=True, boss_active=True))
        finally:
            r.close()
    report = dict(passed=True, checks=checks, core=str(CORE), core_sha256=hashlib.sha256(CORE.read_bytes()).hexdigest(), rom_sha256=hashlib.sha256((ROOT / 'out/release/rom.bin').read_bytes()).hexdigest(), scope=__doc__.strip())
    (ROOT / 'reports/boss-edge-jump-runtime-tests.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', type=int, choices=range(5))
    run(parser.parse_args().case)
