"""Compile four source nine-byte death sequences into native sprite frames."""
from arcade_source import Source,ROOT
import json
def generate(s):
 s.expect(None,0x2253,'21ccb11100f4014000edb0')
 t=s.read(6,0xb1cc,64);assert t[61:]==bytes.fromhex('01079c')
 profiles=[]
 for pc in (0x9c11,0x9d3b,0x9e65,0x9f8f):
  frames=[]
  while True:
   if s.read(7,pc,1)[0]==255:break
   raw=s.read(7,pc,9);assert raw[0] not in (0,254)
   frame=dict(ticks=raw[0],code=[raw[1]|((raw[2]&224)<<3),raw[5]|((raw[6]&224)<<3)],palette=[raw[2]&7,raw[6]&7],flip=[(raw[2]>>3)&1,(raw[6]>>3)&1],dx=[int.from_bytes(raw[3:4],signed=True),int.from_bytes(raw[7:8],signed=True)],dy=[int.from_bytes(raw[4:5],signed=True),int.from_bytes(raw[8:9],signed=True)])
   assert frame['flip'][1]==0
   frames.append(frame);pc+=9
  assert len(frames)==33 and sum(f['ticks'] for f in frames)==328
  profiles.append(frames)
 rows=[]
 for frames in profiles:
  rows.append('{'+','.join('{%s,%d,%s,%s,%s,%s}'%('{' + ','.join(map(str,f['code']))+'}',f['ticks'],*['{'+','.join(map(str,f[k]))+'}' for k in ('palette','flip','dx','dy')]) for f in frames)+'}')
 (ROOT/'src/player_death_data.inc').write_text('/* Generated source sprite animation data. */\nstatic const PlayerDeathFrame death_frames[4][33]={\n'+',\n'.join(rows)+'\n};\n')
 data=dict(source_set=s.lock['aggregate_sha256'],profiles=profiles,witnesses=list(s.witnesses.values()));(ROOT/'reference/player_death.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':generate(Source())
