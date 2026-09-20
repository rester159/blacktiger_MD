"""Compile witnessed constructor data, never scan adjacent machine code for templates.
The oracle covers controlled initial states only. Native AI remains a separate porting task.
"""
import json
from arcade_source import ROOT
from extract_animation import compile_clip

def load(source):
 report=json.loads((ROOT/'reference/constructors.json').read_text())
 assert report['source_set']==source.lock['aggregate_sha256']
 # Shared weapon collision consumes +0E; +10/+11 are bounds, not health.
 source.expect(None,0x321a,'3a0df447dd7e0e9028063804dd770ec9')
 contracts={}
 for r in report['records']:
  templates={}
  for copy in r['copies']:
   raw=bytes.fromhex(copy['bytes'])
   assert source.read(r['bank'],copy['template_address'],len(raw))==raw
   source.expect(r['bank'],copy['copy_pc'],'edb0')
   templates[copy['template_address']]=raw
  states=[];screen_targets=set();contacts=set()
  for result in r['results']:
   for entry in filter(None,result['actors'].split(',')):
    addr,raw=entry.split(':');raw=bytes.fromhex(raw)
    pieces=[raw] if len(raw)<96 else [raw[i:i+48] for i in range(0,len(raw),48)]
    for a in pieces:
     if a[24:26]==bytes.fromhex('58ec'):
      states.append(a)
      address=int(addr,16)
      pool=32 if 0xf520<=address<0xf940 else 48 if 0xf940<=address<0xfc10 else 0
      contacts.add((pool,a[16],a[17]))
      screen_targets.add(pool in (32,48) and (a[13]&127) in ({0,42,52} if pool==32 else {0,35,38}))
  # Refuse a value if constructor profiles disagree. Dynamic templates stay explicit.
  hp={a[14] for a in states};sizes={len(a) for a in states}
  initial=[]
  for frame in r['frames']:
   a=bytes.fromhex(frame['bytes'])
   if a[24:26]!=bytes.fromhex('58ec'):continue
   cursor=int.from_bytes(a[30:32],'little')
   clip=compile_clip(source,a[19],cursor)
   if not clip['frames']:continue
   f=clip['frames'][0];display=bytes.fromhex(frame['display'])
   code=display[0]|((display[1]&224)<<3)
   # Medium sprites put base+1 first when flipped; small ones keep base.
   assert code==f['code']+(int(f['flip']) if len(display)==16 else 0)
   assert display[1]&7==f['palette']
   initial.append((f['code'],f['palette'],len(display)//4))
  first=set(initial)
  categories={a[11] for a in states}
  c={'contact':dict(zip(('pool','half_width','half_height'),next(iter(contacts)))) if len(contacts)==1 else None,'screen_attack_target':next(iter(screen_targets)) if len(screen_targets)==1 else None,'category':next(iter(categories)) if len(categories)==1 else None,'templates':[{'address':pc,'size':len(raw)} for pc,raw in templates.items()],
     'health':next(iter(hp)) if len(hp)==1 else None,
     'initial_frame':dict(zip(('code','palette','pieces'),next(iter(first)))) if len(first)==1 else None,
     'profile_dependent_graphics':len(first)>1,
     'scope':'Observed initial state; AI, hitboxes and later animation not verified.'}
  contracts[(r['bank'],r['constructor'])]=c
 return contracts
