#!/usr/bin/env python3
"""Spatial encounter survey and repeatable presentation traces on the linked ROM.

Only setup is injected, while paused. Measurement uses controller input and native
spawning/AI. This samples map encounters, not complete human playthroughs.
"""
import argparse, hashlib, json, struct, sys, time
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tests'))
from test_runtime import ROOT, Runner, state, put
from run_rom import CORE
from cadence_stats import cadence_stats

def locations():
    data=(ROOT/'src/data.c').read_text()
    import re
    result=[]
    for level in range(8):
        width=1024 if level==2 else 2048
        height=2048 if level==2 else 1024
        collision=np.frombuffer((ROOT/f'res/generated/collision{level}.bin').read_bytes(),np.uint8).reshape(height//16,width//16)
        match=re.search(r'const Spawn spawn'+str(level)+r'\[\]=\{(.*?)\};',data,re.S)
        if not match: raise ValueError('spawn table not found')
        spawns=[tuple(map(int,row)) for row in re.findall(r'\{(\d+),(\d+),(\d+),(\d+)\}',match[1])]
        seen=set()
        for x,y,definition,persistent in spawns:
            bucket=(x//256,y//224)
            if bucket in seen:continue
            floors=[]
            for yy in range(max(2,y//16-5),min(height//16,y//16+7)):
                for xx in range(max(1,x//16-4),min(width//16-1,x//16+5)):
                    if collision[yy,xx]>=2 and not (collision[yy-2:yy,xx:xx+2]>=2).any():
                        floors.append((abs(xx*16-x)+abs(yy*16-y),xx*16,yy*16-32))
            if floors:
                _,px,py=min(floors);seen.add(bucket)
                result.append(dict(name=f'l{level+1}_{px}_{py}',level=level,x=px,y=py))
    return result

def setup(case,rom,symbols):
    r=Runner(rom,skip_boot=False)
    if symbols:
        r.symbols={v[2]:int(v[0],16) for line in symbols.read_text().splitlines() if len(v:=line.split())>=3}
        for k,v in list(r.symbols.items()):
            if '.lto_priv.' in k:r.symbols.setdefault(k.split('.lto_priv.')[0],v)
    for _ in range(120):
        r.run(1)
        if int.from_bytes(r.read('boot_tick'),'big')>=1:break
    r.run(2,8)
    for _ in range(90):
        r.run(1)
        if r.read('boot_done',1)==b'\x01':break
    r.run(100);r.start_game(exploration=True);r.run(30)
    r.run(3,8);r.run(20)
    s=state(r);s.round=case['level'];s.mode=4;s.mode_timer=0;put(r,s);r.run(80)
    r.run(3,8);r.run(20);s=state(r)
    assert s.mode==2
    s.p.x=case['x']*256;s.p.y=case['y']*256;s.p.vx=s.p.vy=0
    s.cam_x=(case['x']-112)&65535;s.cam_y=max(0,min((2048 if case['level']==2 else 1024)-224,case['y']-144))
    # A clean encounter: native spawners initialize all actor-specific state.
    for a in s.actors:a.active=0
    for q in s.shots:q.active=0
    for i in range(160):s.spawned[i]=0
    put(r,s);r.run(20);r.run(3,8);r.run(120)
    return r

def measure(case,rom,symbols,frames,profiler=None,cpu_window=None):
    r=setup(case,rom,symbols)
    if profiler and cpu_window is None:profiler.begin(r)
    cpu=None
    prev=state(r);shown=int.from_bytes(r.read('pacing_presentations',4),'big');sample=-1
    definitions=json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions']
    trace=[];costs=[];changed=0;image=r.frame[40:192].copy();wall=time.monotonic()
    counters={k:int.from_bytes(r.read(k,4 if k.startswith('pacing') else 2),'big') for k in ('pacing_discarded_ticks','vblank_flush_overruns','video_cache_faults')}
    discarded=counters['pacing_discarded_ticks']
    for frame in range(frames):
        if profiler and cpu_window and frame==cpu_window[0]:profiler.begin(r)
        if profiler and cpu_window and frame==sum(cpu_window):cpu=profiler.end()
        # Long enough sweeps to cross tiles, alternating jump/climb/combat and
        # non-attacking passes so surviving enemy groups are represented.
        mask=(128 if frame%360<180 else 64)
        if frame%120<12:mask|=1
        if frame%240<90:mask|=16
        if frame%600>=300 and frame%24<10:mask|=2
        r.run(1,mask);s=state(r)
        current=int.from_bytes(r.read('pacing_presentations',4),'big')
        cx=(s.cam_x+32768)%65536-32768
        visible=sum(bool(a.active) and -64<a.x//256-cx<256 and -64<a.y//256-s.cam_y<224 for a in s.actors)
        active=prev.mode==s.mode==1 and prev.round==s.round==case['level']
        delta=current-shown
        different=not np.array_equal(image,r.frame[40:192]);changed+=different;image=r.frame[40:192].copy()
        enemies=sum(bool(a.active) and definitions[a.definition]['kind'] in (0,1,2,3,4,8) and -64<a.x//256-cx<256 and -64<a.y//256-s.cam_y<224 for a in s.actors)
        debt=int.from_bytes(r.read('pacing_discarded_ticks',4),'big')
        trace.append([int(active),delta,(s.frame-prev.frame)&65535,visible,s.mode,cx,s.cam_y,s.p.x//256,s.p.y//256,int(different),sum(bool(a.active) for a in s.actors),enemies,int.from_bytes(r.read('debug_fps'),'big'),(debt-discarded)&0xffffffff])
        discarded=debt
        serial=int.from_bytes(r.read('profile_samples'),'big')
        if serial!=sample:
            costs.append([frame,*struct.unpack('>3H',r.read('frame_cost',6)),*struct.unpack('>3H',r.read('video_cost',6)),int.from_bytes(r.read('video_dma_bytes'),'big')]);sample=serial
        prev=s;shown=current
    if profiler and (cpu_window is None or cpu is None):cpu=profiler.end()
    windows=[(sum(t[1] for t in trace[i:i+60]),i) for i in range(len(trace)-59) if all(t[0] for t in trace[i:i+60])]
    intervals=[];gap=0;seen=False
    for t in trace:
        if not t[0]:gap=0;seen=False;continue
        gap+=1
        if t[1]:
            if seen:intervals.append(gap)
            seen=True;gap=0
    play=[t for t in trace if t[0]]
    result={**case,'refreshes':frames,'play_refreshes':len(play),'presentations':sum(t[1] for t in play),'mean_fps':round(60*sum(t[1] for t in play)/len(play),2) if play else None,'worst_second':min(windows)[0] if windows else None,'worst_second_at':min(windows)[1] if windows else None,'interval_histogram':dict(Counter(intervals)),'actor_histogram':dict(Counter(t[3] for t in play)),'image_changes':changed,'host_seconds':round(time.monotonic()-wall,3),'trace':trace,'sampled_costs':costs}
    for k,v in counters.items():result[k]=int.from_bytes(r.read(k,4 if k.startswith('pacing') else 2),'big')-v
    result['cadence']=cadence_stats(trace)
    if cpu:
        result['cpu']=cpu
        result['cpu_window']=dict(start_refresh=cpu_window[0] if cpu_window else 0,refreshes=cpu_window[1] if cpu_window else frames)
    r.close();return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,default=ROOT/'out/release/rom.bin');p.add_argument('--symbols',type=Path)
    p.add_argument('--frames',type=int,default=600);p.add_argument('--scene',action='append');p.add_argument('--output',type=Path,default=ROOT/'reports/encounter-profile.json')
    p.add_argument('--cpu-window',type=lambda s:tuple(map(int,s.split(':'))));p.add_argument('--cpu',action='store_true');p.add_argument('--list',action='store_true')
    args=p.parse_args();cases=locations()
    if args.cpu_window and (not args.cpu or len(args.cpu_window)!=2 or args.cpu_window[0]<0 or args.cpu_window[1]<=0 or sum(args.cpu_window)>args.frames):p.error('--cpu-window requires --cpu and START:COUNT within measured refreshes')
    if args.scene:cases=[c for c in cases if c['name'] in args.scene]
    if args.list:print(json.dumps(cases,indent=2));return
    profiler=None
    if args.cpu:
        from profile_cpu import CPUProfiler
        profiler=CPUProfiler(args.symbols or ROOT/'out/release/symbol.txt')
    report=dict(rom_sha256=hashlib.sha256(args.rom.read_bytes()).hexdigest(),core_sha256=hashlib.sha256(CORE.read_bytes()).hexdigest(),scope='Spatially distributed source-spawn encounters, injected paused setup, native AI and controller-only measurement. Not complete playthroughs or host display timing.',trace_columns=['continuous_play','presentations','logic_steps','visible_actors','mode','camera_x','camera_y','player_x','player_y','image_changed','active_actors','visible_enemies','hud_fps','discarded_logic_ticks'],cost_columns=['refresh','game','video','audio','terrain','sprites','overlay','dma_bytes'],cost_units='76800 subticks/second; sampled outer iterations, not per-refresh exclusive costs',cases=[])
    for case in cases:
        result=measure(case,args.rom,args.symbols,args.frames,profiler,args.cpu_window);report['cases'].append(result)
        print({k:v for k,v in result.items() if k not in ('trace','sampled_costs','cpu','cadence')},flush=True)
        args.output.write_text(json.dumps(report,separators=(',',':'))+'\n')
if __name__=='__main__':main()
