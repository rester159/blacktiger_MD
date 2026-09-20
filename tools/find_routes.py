#!/usr/bin/env python3
"""Find terrain routes using production native movement and bonus routines.
This bounded, approximate search excludes combat and is NOT a playthrough test.
"""
import argparse,ctypes as C,hashlib,heapq,itertools,json,re,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BOSSES=[(4,0x9eb1),(4,0x9f16),(3,0x8000),(1,0x9fc4),(1,0x98a3),(3,0x991d),(1,0x98e8),(3,0x9b24)]
ACTIONS=(0,1,2,4,8,9,10,32,33,34,40,41,42)
def xy(raw):
 word=lambda at:int.from_bytes(raw[at:at+2],sys.byteorder)
 return (word(0)+word(4))%65536,(word(2)+word(6))%65536

def build(folder,meta):
 source=(ROOT/'src/data.c').read_text();rows=re.findall(r'const Bonus(?:Patch|Round) .*?;',source)
 assert len(rows)==9
 rows.append('const Round rounds[8]={'+','.join('{.width=%d,.height=%d}'%(r['width'],r['height']) for r in meta['rounds'])+'};')
 for name in ('contact_player_width','contact_player_height'):rows.append('const u8 '+re.search(name+r'=\d+',source)[0]+';')
 (folder/'route_data.inc').write_text('\n'.join(rows))
 contact=(ROOT/'src/hazard.c').read_text();(folder/'route_contact.inc').write_text(contact[contact.index('u8 player_contact'):contact.index('u8 actor_contact')])
 binary=folder/'route.dylib'
 subprocess.run(['cc','-shared','-fPIC','-O2','-DHOST_TEST','-I'+str(ROOT/'inc'),'-I'+str(folder),str(ROOT/'src/player_motion.c'),str(ROOT/'src/bonus.c'),str(ROOT/'tools/route_model.c'),'-o',str(binary)],check=True)
 lib=C.CDLL(str(binary));lib.setup.argtypes=[C.c_char_p,C.c_int,C.c_int,C.c_int]
 return lib,source

def search(lib,source,meta,level,args):
 State=C.c_ubyte*lib.state_size();r=meta['rounds'][level];cells=(ROOT/f'res/generated/collision{level}.bin').read_bytes()
 original_hash=hashlib.sha256(cells).hexdigest()
 if args.open_walls:
  cells=bytearray(cells)
  patches=re.search(r'const WorldPatch patches'+str(level)+r'\[\]=\{(.*?)\};',source,re.S)[1]
  value=int(re.search(r'patches'+str(level)+r',open_tile'+str(level)+r',\d+,(\d+)',source)[1])
  opened=set()
  for cell,_ in re.findall(r'\{(\d+),(\d+)\}',patches):
   cell=int(cell);opened.update((cell,cell+r['width']//16));cells[cell]=cells[cell+r['width']//16]=value
  bonus=re.search(r'const BonusPatch bonus_patches'+str(level)+r'\[\]=\{(.*?)\};',source,re.S)[1]
  assert opened.isdisjoint(int(cell) for cell in re.findall(r'\{(\d+),\{\{',bonus)), 'Overlapping patches require post-bonus wall application'
  cells=bytes(cells)
 lib.setup(cells,r['width'],r['height'],level)
 rows=[list(map(int,x.split(','))) for x in re.findall(r'\{([^{}]+)\}',re.search(r'const Spawn spawn'+str(level)+r'\[\]=\{(.*?)\};',source,re.S)[1])]
 defs=meta['actor_definitions'];target=next(row for row in rows if (defs[row[2]]['bank'],defs[row[2]]['address'])==BOSSES[level]);tx,ty=target[:2]
 initial=State();lib.start(initial,r['camera'][0]+112,r['camera'][1]+144)
 def key(p):
  x,y=xy(p)
  # Coarsening prunes search, never edits a simulated state. Failure is inconclusive.
  return (x//args.quantum,y//args.quantum,p[10],p[11],p[15],p[17],p[19],p[21],p[22],p[28]&3,bytes(p[30:36]))
 def heuristic(p):
  x,y=xy(p);return max(0,abs(x-tx)-96)/2+max(0,abs(y-ty)-64)/4
 ids=itertools.count();heap=[(heuristic(initial),next(ids),0,bytes(initial),-1,0)];visited={};nodes=[];begin=time.monotonic();found=None
 while heap and len(nodes)<args.limit:
  _,_,cost,raw,parent,action=heapq.heappop(heap);p=State.from_buffer_copy(raw);k=key(p)
  if visited.get(k,1e9)<=cost:continue
  visited[k]=cost;index=len(nodes);nodes.append((raw,parent,action));x,y=xy(p)
  if abs(x-tx)<=96 and abs(y-ty)<=64:found=index;break
  for action in ACTIONS:
   q=State.from_buffer_copy(raw)
   if not lib.advance(q,action,args.ticks):continue
   if visited.get(key(q),1e9)<=cost+args.ticks:continue
   heapq.heappush(heap,(cost+args.ticks+heuristic(q)*2,next(ids),cost+args.ticks,bytes(q),index,action))
 path=[]
 if found is not None:
  while nodes[found][1]!=-1:
   raw,parent,action=nodes[found];path.append(dict(input=action,ticks=args.ticks,position=xy(raw),state=raw.hex()));found=parent
  path.reverse()
  # Replay from the initial state, independent of search parent/visited structures.
  lib.setup(cells,r['width'],r['height'],level);p=State.from_buffer_copy(initial)
  for step in path:
   assert lib.advance(p,step['input'],step['ticks']) and bytes(p).hex()==step['state']
 report=dict(settings=dict(limit=args.limit,ticks=args.ticks,quantum=args.quantum,open_walls=args.open_walls),round=level+1,found=bool(path),nodes=len(nodes),limit_reached=len(nodes)>=args.limit,seconds=round(time.monotonic()-begin,3),target=target,initial=bytes(initial).hex(),ticks=len(path)*args.ticks,collision_sha256=original_hash,simulated_collision_sha256=hashlib.sha256(cells).hexdigest(),path=path)
 return report

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--open-walls',action='store_true',help='Diagnostic only: pre-open hidden walls; does not prove they can be opened in gameplay.');parser.add_argument('--round',type=int,choices=range(1,9),action='append');parser.add_argument('--limit',type=int,default=180000);parser.add_argument('--ticks',type=int,default=8);parser.add_argument('--quantum',type=int,default=8);args=parser.parse_args()
 assert args.limit>0 and args.ticks>0 and args.quantum>0
 meta=json.loads((ROOT/'reports/assets.json').read_text());out=ROOT/('reports/routes-open-walls' if args.open_walls else 'reports/routes');out.mkdir(exist_ok=True);reports=[]
 with tempfile.TemporaryDirectory() as folder:
  lib,source=build(Path(folder),meta)
  for level in [r-1 for r in args.round or range(1,9)]:
   report=search(lib,source,meta,level,args);(out/f'round{level+1}.json').write_text(json.dumps(report,indent=2)+'\n');summary={k:v for k,v in report.items() if k not in ('path','initial')};reports.append(summary);print(json.dumps(summary),flush=True)
 report=dict(scope='Bounded approximate terrain search using native movement, trigger contacts, alternate-area destinations and animated collision. Includes endpoint replay. Excludes enemies, combat-driven wall opening, shops, death and boss victory; --open-walls assumes hidden walls are already open for diagnosis; not proof of natural completion. A failed search does not prove a map unreachable.',settings=vars(args),sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('src/player_motion.c','src/bonus.c','src/hazard.c','src/data.c','tools/route_model.c')},rounds=reports)
 (ROOT/('reports/route-search-open-walls.json' if args.open_walls else 'reports/route-search.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
