"""Linked-ROM traversal, source-map rendering, seed variation and exit isolation."""
import ctypes as C,json,hashlib
from test_runtime import ROOT,Runner,state,put,BE,U8,U16,U32
class Dungeon(BE):
 _fields_=[('seed',U32),('streams',U32*8),*[(k,U32) for k in ('clock','run_xp','banked_xp','score','zenny')],*[(k,U16) for k in ('timer','freeze','kills','last_kills','deaths','revision','seen_revision')],*[(k,U8) for k in ('active','phase','stage','max_hp','charges','cleared','banked','scene_reload','boon','rank')]]
class Layout(BE):_fields_=[('ready',U8),('count',U8),('source',U8),('ids',U8*10),('exit',U16)]
def dstate(r):return Dungeon.from_buffer_copy(r.read('dungeon',C.sizeof(Dungeon)))
def tap(r,b):r.run(4,b);r.run(4)
ref=json.loads((ROOT/'reference/dungeon_chunks.json').read_text());routes=[]
for seed in range(1,9):
 r=Runner(ROOT/'out/release/rom.bin');r.run(100);tap(r,32);tap(r,8);tap(r,32);tap(r,32);tap(r,8)
 d=dstate(r);d.seed=seed;r.write('dungeon',0,bytes(d));tap(r,8);r.run(160)
 d=Layout.from_buffer_copy(r.read('dungeon_layout',C.sizeof(Layout)));ids=list(d.ids[:d.count])
 s=state(r);s.p.invincible=60000
 for i in range(160):s.spawned[i]=2
 for a in s.actors:a.active=0
 put(r,s);r.run(8)
 # First chunk starts at x=0. Replay certified controller inputs through joypad.
 frames=0
 for k,i in enumerate(ids):
  for raw in ref['chunks'][i]['path']:
   buttons=(128 if raw&1 else 0)|(1 if raw&32 else 0)|(16 if raw&8 else 0)
   old=state(r).frame
   for _ in range(6):
    r.run(1,buttons);frames+=1
    if state(r).frame!=old:break
   else:raise AssertionError('logic stalled')
  r.run(3);s=state(r);target=min((k+1)*256,d.exit+16)
  assert abs(s.p.x//256-target)<=16 and s.p.y//256==672,(seed,k,i,s.p.x//256,s.p.y//256,target)
  if k==2:r.capture(f'dungeon-generated-seed-{seed}.png')
 assert int.from_bytes(r.read('video_cache_faults'),'big')==0
 # The final socket is explicit: Up opens the run's gate, not an arcade exit.
 tap(r,16);assert dstate(r).phase==4
 routes.append(dict(seed=seed,source=d.source,chunks=ids,video_frames=frames))
 # Back out after expiry, then normal Play must use original level zero.
 if seed==1:
  tap(r,8);r.run(160);ds=dstate(r);ds.clock=1;r.write('dungeon',0,bytes(ds));r.run(6);tap(r,1)
  assert not Layout.from_buffer_copy(r.read('dungeon_layout',C.sizeof(Layout))).ready
 r.close()
assert len({tuple(x['chunks']) for x in routes})==8
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),routes=routes,scope=__doc__,note='Enemies disabled for collision-route replay; combat and NPCs are separate subsystem tests.')
(ROOT/'reports/dungeon-layout-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
