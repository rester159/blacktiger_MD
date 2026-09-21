"""Original character HUD; fixed HUD colors constrain shared object palettes."""
import json,itertools
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STYLES=(0,2,3,4,5,6,7,8,9,10,11,18,20,25)
def observed():
 line=next(l for l in (ROOT/'reference/hud_oracle_events.txt').read_text().splitlines() if l.startswith('HUD|'))
 return tuple(map(bytes.fromhex,line.split('|')[1:]))
def color(p,i):return ((p[i]>>5)<<1)|(((p[i]&15)>>1)<<5)|(((p[1024+i]&15)>>1)<<9)
def rgb(w):return np.array([(w>>1)&7,(w>>5)&7,(w>>9)&7])
def palettes(hero,enemy):
 _,p,_=observed();groups=[set(color(p,768+b*4+i) for i in range(3)) for b in STYLES]
 best=None
 distance={(int(c),v):int(np.sum((rgb(c)-rgb(v))**2)) for c in set(hero+enemy) for v in set.union(*groups,{0,0xeee},set(hero+enemy))}
 for mask in range(1<<len(groups)):
  a={0,0xeee};b={0,0xeee}
  for i,g in enumerate(groups):(a if mask>>i&1 else b).update(g)
  if len(a)>15 or len(b)>15:continue
  # Keep spare slots for the most poorly represented original actor colors.
  for values,colors in ((a,hero),(b,enemy)):
   while len(values)<15:
    err=[min(distance[int(c),v] for v in values) for c in colors]
    c=colors[int(np.argmax(err))]
    if c in values:break
    values.add(c)
  loss=sum(min(distance[int(c),v] for v in a) for c in hero)*4+sum(min(distance[int(c),v] for v in b) for c in enemy)
  key=(loss,mask)
  if best is None or key<best[0]:best=(key,a,b)
 assert best
 result=[]
 for values in best[1:]:
  mid=sorted(values-{0,0xeee});result.append([0,0]+mid+[0]*(13-len(mid))+[0xeee])
 return result
