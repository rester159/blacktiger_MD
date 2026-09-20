#!/usr/bin/env python3
"""Replay a round-one terrain plan from the title with controller input only.
Records the actual video-frame input tape and result; never writes game RAM.
"""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from test_runtime import Runner,state
from find_routes import BOSSES

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',type=Path,default=ROOT/'reports/routes/round1.json');parser.add_argument('--air-attack',action='store_true');args=parser.parse_args()
 plan=json.loads(args.plan.read_text());assert plan['round']==1 and plan['found'],'A fresh-title replay requires a found round-one plan.'
 rom=ROOT/'out/release/rom.bin';r=Runner(rom);defs=json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions'];tape=[];trace=[];outcome='plan_exhausted';previous=0
 def run(mask):
  r.run(1,mask)
  if tape and tape[-1][0]==mask:tape[-1][1]+=1
  else:tape.append([mask,1])
 for _ in range(100):run(0)
 for _ in range(2):run(8)
 for i,step in enumerate(plan['path']):
  raw=step['input'];mask=(128 if raw&1 else 0)|(64 if raw&2 else 0)|(32 if raw&4 else 0)|(16 if raw&8 else 0)|(1 if raw&32 else 0)
  first=state(r).frame
  for _ in range(120):
   s=state(r);keys=mask
   if args.air_attack and i%3==0 and r.read('player_motion',30)[15]:keys|=2
   run(keys);previous=keys;s=state(r)
   if s.mode!=1 or ((s.frame-first)&65535)>=step['ticks']:break
  row=dict(step=i,logic_frame=s.frame,position=[s.p.x//256,s.p.y//256],expected=step['position'],mode=s.mode,armor=s.p.armor,hp=s.p.hp,lives=s.p.lives);trace.append(row)
  if any(a.active and (defs[a.definition]['bank'],defs[a.definition]['address'])==BOSSES[0] for a in s.actors):outcome='boss_spawned';break
  if s.mode!=1:outcome={3:'shop',4:'death',5:'round_clear',8:'rescue'}.get(s.mode,'mode_transition');break
 r.capture('route-replay.png');final_state=bytes(state(r));r.close()
 # Verify the saved controller tape reproduces the result from a fresh boot.
 verify=Runner(rom)
 for mask,count in tape:verify.run(count,mask)
 assert bytes(state(verify))==final_state,'Input tape failed deterministic replay'
 verify.close()
 report=dict(rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),plan_sha256=hashlib.sha256(args.plan.read_bytes()).hexdigest(),tape_verified=True,final_state_sha256=hashlib.sha256(final_state).hexdigest(),policy=dict(air_attack=args.air_attack),outcome=outcome,video_frames=sum(n for _,n in tape),input_tape=tape,trace=trace,scope='Fresh title, controller input only, no RAM injection or savestate loading. A terrain plan replay is not a full-game validation; boss_spawned does not mean boss defeated.')
 (ROOT/'reports/route-replay.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('rom_sha256','outcome','video_frames','policy')}))
if __name__=='__main__':main()
