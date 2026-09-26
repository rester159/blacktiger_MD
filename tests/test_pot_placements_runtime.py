"""Visit every source pot location in the linked cartridge (injected cameras)."""
import json
from test_runtime import ROOT,Runner,state,put
from test_pots_runtime import pot,pause,resume
DATA=json.loads((ROOT/'reference/pots.json').read_text())
def run():
 checked=0
 for level,rows in enumerate(DATA['placements']):
  r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(3);r.run(80);pause(r)
  s=state(r);s.round=level;s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(100)
  for x,y,pid in rows:
   pause(r);s=state(r);s.p.x=(x-64)*256;s.p.y=(y-8)*256;s.p.vx=s.p.vy=0;s.p.invincible=10000;s.p.exploration=1
   s.cam_x=max(0,x-128);s.cam_y=max(0,min((2048 if level==2 else 1024)-224,y-112))
   for a in s.actors:a.active=0
   for i in range(160):s.spawned[i]=2
   put(r,s);r.write('pots',0,bytes(660));r.write('pots_end',0,b'\0');r.run(10);resume(r,8)
   live=[pot(r,i) for i in range(33) if pot(r,i)['active'] and pot(r,i)['id']==pid]
   assert len(live)==1,(level,x,y,pid,live,state(r).mode,state(r).cam_x,state(r).cam_y)
   p=live[0];width=1024 if level==2 else 2048;height=2048 if level==2 else 1024
   assert any(p['x']%width==rx and p['y']%height==ry for rx,ry,rid in rows if rid==pid),(level,p)
   checked+=1
  r.capture(f'pots-level-{level+1}.png');r.close()
 print(f'PASS: all {checked} arcade pot placements spawn; shared persistence IDs do not duplicate.')
if __name__=='__main__':run()
