import json
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source();cases=[]
# Shared floor, pit, wall, platform, ceiling and ladder geometries; input changes
# include a vertical jump followed by air steering and release/repress edges.
patterns=[[0],[1],[2],[4],[5],[6],[8],[9],[10],[32],[33],[34],[41],[42],
          [32]*12+[1]*30+[0]*18,[32]*12+[2]*30+[0]*18,
          [8]*20+[33]*20+[0]*20,[8]*20+[34]*20+[0]*20,
          [4]*15+[0]*15+[1]*15+[32]*15,
          [33]*10+[0]*2+[33]*10+[0]*38]
for geometry in range(7):
 for reversed in range(2):
  for pattern in patterns:
   cases.append(dict(geometry=geometry,reversed=reversed,x=384,y=400,ladder=0,falling=0,pattern=pattern,ticks=80))
for geometry in (0,1,5,6):
 for pattern in ([0],[4],[8],[33],[34],[40]):
  cases.append(dict(geometry=geometry,reversed=0,x=392,y=352,ladder=1,falling=0,pattern=pattern,ticks=80))
for y in (351,352,399,400,401):
 cases.append(dict(geometry=0,reversed=0,x=384,y=y,ladder=0,falling=1,pattern=[0],ticks=60))
for geometry in (0,2,5):
 for tier in range(5):
  for reversed in (0,1):
   for pattern in ([16],[17],[18],[20],[21],[22],[24],[48],[49],[50],
                   [32]*10+[17]*20+[0]*50,[8]*10+[49]*20+[0]*50,
                   [17]*12+[0]*2+[18]*12+[0]*54):
    cases.append(dict(geometry=geometry,reversed=reversed,x=384,y=400,ladder=0,falling=0,pattern=pattern,ticks=80,attack=1,tier=tier,hit=0))
for tier in range(5):
 for tick in (7,10,15,24):
  cases.append(dict(geometry=0,reversed=0,x=384,y=400,ladder=0,falling=0,pattern=[17],ticks=45,attack=1,tier=tier,hit=tick))
def lua(v):
 if isinstance(v,dict):return '{'+','.join(k+'='+lua(x) for k,x in v.items())+'}'
 if isinstance(v,list):return '{'+','.join(map(lua,v))+'}'
 return str(v)
t=s.read(4,0xb63a,2048)
lines,report=run_oracle(s,'player-motion-oracle','return '+lua(dict(tiles=[t.index(i) for i in range(4)],cases=cases)))
report['cases']=cases
report['witnesses']=[s.read(7,0x90a6,0x70).hex(),s.read(7,0x9112,4).hex()]
(ROOT/'reference/player_motion_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(len(lines)-1)
