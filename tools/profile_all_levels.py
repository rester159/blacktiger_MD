import sys,struct,json,statistics,hashlib,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_runtime import ROOT,Runner,state,put
parser=argparse.ArgumentParser(description='Deterministic NTSC load samples across all eight levels and Boss Rush.')
parser.add_argument('--rom',type=Path,default=ROOT/'out/release/rom.bin')
parser.add_argument('--symbols',type=Path,default=ROOT/'out/release/symbol.txt')
parser.add_argument('--output',type=Path,default=ROOT/'reports/all-level-performance.json')
args=parser.parse_args();rom=args.rom;cases=[]
for level,cx,cy,name in [(i,None,None,f'level{i+1}_entry') for i in range(8)]+[(3,512,304,'cave_middle'),(5,976,656,'sky_middle'),(6,784,304,'windows_middle'),(7,832,64,'palace_upper'),(7,784,448,'palace_lower'),(7,896,736,'palace_blue'),(7,0,0,'rush1'),(7,4,0,'rush5'),(7,7,0,'rush8')]:
 r=Runner(rom,skip_boot=False)
 r.symbols={v[2]:int(v[0],16) for line in args.symbols.read_text().splitlines() if len(v:=line.split())>=3}
 for k,v in list(r.symbols.items()):
  if '.lto_priv.' in k:r.symbols.setdefault(k.split('.lto_priv.')[0],v)
 for _ in range(120):
  r.run(1)
  if int.from_bytes(r.read('boot_tick'),'big')>=1:break
 r.run(2,8)
 for _ in range(90):
  r.run(1)
  if r.read('boot_done',1)==b'\1':break
 r.run(100)
 if name.startswith('rush'):
  for key in (32,8,32,8):r.run(8,key);r.run(8)
  r.write('boss_rush',1,bytes([cx]));s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(40)
 else:
  r.start_game();s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(40)
  if cx is not None:
   s=state(r);s.p.x=(cx+112)*256;s.p.y=(cy+144)*256;s.cam_x=cx;s.cam_y=cy;s.p.vx=s.p.vy=0;put(r,s);r.run(30)
 s=state(r);s.p.invincible=30000;s.p.hp=4;put(r,s);start=s.frame;prev=start;cost=[];vcost=[];dma=[];gaps=[];gap=0
 for frame in range(600):
  direction=128 if frame%400<200 else 64
  r.run(1,direction|2);s=state(r);gap+=1
  if s.frame!=prev:
   cost.append(struct.unpack('>3H',r.read('frame_cost',6)));vcost.append(struct.unpack('>3H',r.read('video_cost',6)));dma.append(int.from_bytes(r.read('video_dma_bytes'),'big'));gaps.append(gap);gap=0;prev=s.frame
 entry=dict(scene=name,updates=(s.frame-start)&65535,frames=600,worst_gap=max(gaps),cost=[int(statistics.median(c[i] for c in cost)) for i in range(3)],video_cost=[int(statistics.median(c[i] for c in vcost)) for i in range(3)],dma_max=max(dma),cache_faults=int.from_bytes(r.read('video_cache_faults'),'big'),vblank_overruns=int.from_bytes(r.read('vblank_flush_overruns'),'big'))
 cases.append(entry);r.close();print(entry,flush=True)
assert all(c['cache_faults']==0 and c['vblank_overruns']==0 for c in cases)
args.output.write_text(json.dumps(dict(passed=True,sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=cases,scope='Deterministic 600-video-frame NTSC samples with repeated movement/attack and invulnerability. Update counts include any intervening game modes; this is not a natural full playthrough or a hardware benchmark.'),indent=2)+'\n')
