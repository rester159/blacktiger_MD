"""Multi-tick camera motion must not blank/reload terrain or corrupt its cache."""
import hashlib
import json
from test_runtime import ROOT, Runner, state, put, check_video_cache

rom = ROOT/'out/release/rom.bin'
cases = []
for level in range(8):
    r = Runner(rom)
    r.run(100)
    r.start_game()
    s = state(r)
    s.round, s.mode, s.mode_timer, s.p.lives = level, 4, 0, 3
    put(r, s)
    r.run(80)
    s = state(r)
    s.mode = 2
    s.cam_x, s.cam_y = 256, 256
    put(r, s)
    r.run(80)
    reloads = r.read('video_reload_count')
    for dx, dy in ((0, 16), (0, -16), (16, 0), (-16, 0), (16, 16),
                   (-16, -16), (16, -16), (-16, 16), (8, 16), (-8, -16), (24, 24), (-24, -24), (32, 32), (-32, -32), (32, -32), (-32, 32)):
        s = state(r)
        s.cam_x += dx
        s.cam_y += dy
        put(r, s)
        r.run(12)
        assert r.read('video_reload_count') == reloads, (level, dx, dy, 'terrain reloaded')
        check_video_cache(r, state(r))
        assert int.from_bytes(r.read('video_cache_faults'), 'big') == 0
        assert int.from_bytes(r.read('vblank_flush_overruns'), 'big') == 0
    cases.append(dict(level=level+1, scrolls=16, no_reload=True, pixels_match=True))
    r.close()
report = dict(passed=True, cases=cases, rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
              scope='Paused injected camera deltas up to four tiles, both axes and all eight terrain caches. '
                    'Actual VRAM matches source tiles after every scroll; no full reload or cache faults.')
(ROOT/'reports/scroll-catchup-runtime-tests.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
