"""Reported level-3 upper corridor: corridor exits and continued ascent through the vertical map seam."""
import hashlib
import json
import struct
from test_runtime import ROOT, Runner, state, put, check_video_cache

def setup():
    r = Runner(ROOT / 'out/release/rom.bin')
    r.run(100)
    r.start_game(exploration=True)
    r.run(20)
    s = state(r)
    s.round, s.mode, s.mode_timer = 2, 4, 0
    put(r, s)
    r.run(80)
    s = state(r)
    s.mode = 2
    put(r, s)
    r.run(20)
    s = state(r)
    s.mode = 1
    s.p.x, s.p.y = 832 * 256, 64 * 256
    s.p.vx = s.p.vy = 0
    s.cam_x, s.cam_y = 720, 0
    put(r, s)
    r.run(30)
    return r


r = setup()
r.capture('level3-reported-corridor.png')
r.run(90, 128)
s = state(r)
assert (s.p.x // 256, s.p.y // 256) == (936, 64), 'original wall moved'
wall_position = [s.p.x // 256, s.p.y // 256]
# Walk left until the player drops into the gap beside the golden pole.
for _ in range(140):
    r.run(1, 64)
    s = state(r)
    if s.p.y // 256 > 64:
        break
else:
    raise AssertionError('cannot enter the left descent gap')
gap_position = [s.p.x // 256, s.p.y // 256]
r.run(90)
s = state(r)
assert s.mode == 1 and s.p.y // 256 >= 160, 'corridor descent blocked'
r.capture('level3-corridor-exit.png')
report = dict(
    passed=True,
    rom_sha256=hashlib.sha256((ROOT / 'out/release/rom.bin').read_bytes()).hexdigest(),
    wall_position=wall_position,
    gap_position=gap_position,
    exit_position=[s.p.x // 256, s.p.y // 256],
    scope='Player placed at screenshot corridor; native actors and controller input thereafter. Debug exploration enabled. Confirms descent, pole jumps and upward traversal through the vertical map seam to two further platforms; validates wrapped actors and resident map tiles. Not a complete level playthrough.',
)
r.close()
# Reproduce the supplied blocked-path screenshot, then reach the top using
# only controller input. Jump at the lip: jumping earlier hits the ceiling.
from PIL import Image
r = setup()
frames = []
def move(count, buttons):
    for frame in range(count):
        r.run(1, buttons)
        if frame % 3 == 0:
            frames.append(Image.fromarray(r.frame))
    s = state(r)
    assert s.mode == 1, 'upper route left gameplay'
    return s

move(30, 0)
s = move(50, 64)  # Left to the lip of the gap.
assert (s.p.x // 256, s.p.y // 256) == (732, 64)
s = move(12, 65)  # Left + jump catches the gold pole.
assert s.p.climb and s.p.y // 256 < 48, 'cannot catch upper pole'
report['pole_position'] = [s.p.x // 256, s.p.y // 256]
move(40, 16)  # Up; release jump before jumping off the pole.
move(35, 129)  # Right + jump onto the platform above the corridor.
s = move(20, 0)
assert s.p.y == 0 and 752 <= s.p.x // 256 < 864 and s.p.grounded, 'upper platform inaccessible'
report['upper_platform_position'] = [s.p.x // 256, s.p.y // 256]
r.capture('level3-upper-route-end.png')
frames[0].save(ROOT / 'reports/level3-upper-route.gif', save_all=True,
               append_images=frames[1:], duration=50, loop=0)
r.close()
# Continue above the former hard ceiling into the bottom-stored map section.
# No terrain edits or player-state injection after this initial screenshot.
r = setup()
frames = []
reloads = int.from_bytes(r.read('video_reload_count'), 'big')
move(30, 0)
move(50, 64)
move(12, 65)
move(15, 16)
move(25, 65)  # Jump left off the pole to the other top ledge.
move(20, 0)
move(12, 1)   # Vertical jump, then steer left at the apex.
move(22, 64)
s = move(20, 0)
assert s.p.y // 256 == -64 and s.p.grounded, 'vertical map join is blocked'
move(12, 1)   # Catch the next pole above the seam.
move(15, 16)
move(35, 129)
s = move(20, 0)
assert s.p.y // 256 == -128 and s.p.grounded, 'cannot continue beyond vertical join'
assert int.from_bytes(r.read('video_reload_count'), 'big') == reloads, 'vertical seam reloaded scenery'
assert int.from_bytes(r.read('video_cache_faults'), 'big') == 0
check_video_cache(r, s)
rom = (ROOT / 'out/release/rom.bin').read_bytes()
wrapped_rows = []
for actor in s.actors:
    if not actor.active:
        continue
    raw_y = struct.unpack_from('>H', rom, r.symbols['spawn2'] + actor.source * 8 + 2)[0]
    if raw_y > 1700 and actor.y // 256 < 0:
        wrapped_rows.append(actor.source)
assert wrapped_rows, 'actors above the vertical seam failed to spawn'
report['vertical_join'] = dict(position=[s.p.x // 256, s.p.y // 256],
    wrapped_actor_rows=wrapped_rows, resident_tiles_match=True, no_reload=True)
r.capture('level3-vertical-progress.png')
frames[0].save(ROOT / 'reports/level3-vertical-progress.gif', save_all=True,
               append_images=frames[1:], duration=50, loop=0)
r.close()
# Downward traversal must use the same map connection, without a death/reset.
r = setup()
s = state(r)
s.mode = 2
s.p.x, s.p.y = 784 * 256, 2000 * 256
s.cam_x, s.cam_y = 672, 1856
put(r, s)
r.run(30)
s = state(r)
s.mode = 1
put(r, s)
r.run(80)
s = state(r)
assert s.mode == 1 and s.p.y // 256 == 2048, 'downward seam caused a fall/reset'
check_video_cache(r, s)
report['downward_join_position'] = [s.p.x // 256, s.p.y // 256]
r.close()
(ROOT / 'reports/level3-corridor-runtime-tests.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
