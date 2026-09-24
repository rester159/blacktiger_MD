#!/usr/bin/env python3
"""Frame-by-frame cadence during uninterrupted PLAY, never menu averages."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from test_runtime import ROOT, Runner, state, put


def measure(rom, symbols, frames=600, scenes=None, exploration=False):
    cases = []
    definitions = json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions']
    for level, cx, cy, name in [(i, None, None, f"level{i+1}_entry") for i in range(8)] + [(3,512,304,"cave_middle"),(5,976,656,"sky_middle"),(6,784,304,"windows_middle"),(7,832,64,"palace_upper"),(7,784,448,"palace_lower")]:
        if scenes is not None and name not in scenes:continue
        r = Runner(rom, skip_boot=False)
        r.symbols = {v[2]: int(v[0], 16) for line in symbols.read_text().splitlines()
                     if len(v := line.split()) >= 3}
        for k, v in list(r.symbols.items()):
            if '.lto_priv.' in k:
                r.symbols.setdefault(k.split('.lto_priv.')[0], v)
        for _ in range(120):
            r.run(1)
            if int.from_bytes(r.read('boot_tick'), 'big') >= 1:
                break
        r.run(2, 8)
        for _ in range(90):
            r.run(1)
            if r.read('boot_done', 1) == b'\1':
                break
        r.run(100)
        r.start_game(exploration=exploration)
        s = state(r)
        s.round, s.mode, s.mode_timer, s.p.lives = level, 4, 0, 3
        put(r, s)
        r.run(60)
        s = state(r)
        if cx is not None:
            s.p.x, s.p.y = (cx+112)*256, (cy+144)*256
            s.cam_x, s.cam_y = cx, cy
            s.p.vx = s.p.vy = 0
            put(r, s)
            r.run(30)
            s = state(r)
        if not exploration:s.p.invincible = 30000
        s.p.hp = 4
        put(r, s)
        overruns=int.from_bytes(r.read("vblank_flush_overruns"),"big")
        trace = []
        previous_image=r.frame[32:].copy()
        image_changes=0
        previous = s
        start = s.frame
        counters = {key: int.from_bytes(r.read(key, 4), 'big')
                    for key in ('pacing_catchup_ticks', 'pacing_discarded_ticks') if key in r.symbols}
        presented = int.from_bytes(r.read('pacing_presentations', 4), 'big') if counters else None
        # Patrol around the starting point: enemies remain alive and run their real AI.
        # No RAM edits during the measurement and no injected enemy implementations.
        for frame in range(frames):
            r.run(1, 128 if ((previous.frame-start)&65535)%60 < 30 else 64)
            image_changes+=not np.array_equal(previous_image,r.frame[32:])
            previous_image=r.frame[32:].copy()
            s = state(r)
            active = previous.mode == s.mode == 1 and previous.round == s.round == level
            camera_x=(s.cam_x+32768)%65536-32768
            actors = sum(a.active and -32 < a.x // 256 - camera_x < 256
                         and -32 < a.y // 256 - s.cam_y < 224 for a in s.actors)
            enemies = sum(a.active and definitions[a.definition]['kind'] in (0, 1, 2, 3, 4, 8)
                          and -32 < a.x // 256 - camera_x < 256
                          and -32 < a.y // 256 - s.cam_y < 224 for a in s.actors)
            delta = (s.frame - previous.frame) & 65535
            timer_steps = previous.time*60-previous.clock-(s.time*60-s.clock)
            shown = int.from_bytes(r.read('pacing_presentations', 4), 'big') if counters else None
            trace.append([int(active), delta, actors, s.mode, enemies, timer_steps,
                          shown-presented if shown is not None else None])
            presented = shown
            previous = s
        play = [row for row in trace if row[0]]
        steps = [row[1] for row in play]
        windows = [sum(row[1] for row in trace[i:i+60]) for i in range(len(trace)-59)
                   if all(row[0] for row in trace[i:i+60])]
        case = dict(scene=name, level=level+1, observed_image_changes=image_changes, play_video_frames=len(play),
                    logic_updates=sum(steps), step_histogram=dict(Counter(steps)),
                    worst_second_updates=min(windows) if windows else None,
                    timer_steps=sum(row[5] for row in play),
                    visible_actor_histogram=dict(Counter(row[2] for row in play)),
                    visible_enemy_histogram=dict(Counter(row[4] for row in play)),
                    trace=trace)
        if 'pacing_catchup_ticks' in r.symbols:
            case['catchup_ticks'] = int.from_bytes(r.read('pacing_catchup_ticks', 4), 'big')-counters['pacing_catchup_ticks']
            case['discarded_ticks'] = int.from_bytes(r.read('pacing_discarded_ticks', 4), 'big')-counters['pacing_discarded_ticks']
            case['presentation_histogram'] = dict(Counter(row[6] for row in play))
        case['vblank_overruns']=(int.from_bytes(r.read('vblank_flush_overruns'),'big')-overruns)&65535
        case['worst_second_presentations']=None if not counters else min((sum(row[6] for row in trace[i:i+60]) for i in range(len(trace)-59) if all(row[0] for row in trace[i:i+60])),default=None)
        intervals=[];gap=0;seen=False
        for row in trace:
            if not row[0]:gap=0;seen=False;continue
            gap+=1
            if row[6]:
                if seen:intervals.append(gap)
                seen=True;gap=0
        case['presentation_interval_histogram']=dict(Counter(intervals))
        case['longest_presentation_gap']=max(intervals,default=0)
        cases.append(case)
        print({k: v for k, v in case.items() if k != 'trace'}, flush=True)
        r.close()
    return dict(rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(), exploration=exploration, cases=cases,
                trace_columns=['continuous_play', 'logic_steps', 'visible_actors', 'mode',
                               'visible_enemies', 'timer_steps', 'presentations'],
                scope='NTSC 30-tick left/right patrol encounters, invulnerable player. '+
                ('Level Select exploration immunity/frozen timer. ' if exploration else 'Temporary damage shield; normal countdown. ')+
                'Real enemy AI; no RAM writes inside each measured sample. '
                'Visible actors include non-enemy objects. Not full routes or hardware validation.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, default=ROOT/'out/release/rom.bin')
    p.add_argument('--symbols', type=Path, default=ROOT/'out/release/symbol.txt')
    p.add_argument('--output', type=Path, default=ROOT/'reports/frame-pacing.json')
    p.add_argument('--frames', type=int, default=600)
    p.add_argument('--exploration', action='store_true', help='Measure actual Level Select exploration rules')
    p.add_argument('--scene', action='append', help='Restrict to one or more named samples')
    a = p.parse_args()
    if a.frames<60:p.error('--frames must be at least 60')
    a.output.write_text(json.dumps(measure(a.rom, a.symbols, a.frames, a.scene, a.exploration), indent=2)+'\n')
