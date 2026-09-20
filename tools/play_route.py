#!/usr/bin/env python3
"""Bounded controller search in the actual ROM; verify chosen tape from fresh boot.
Forked process copies explore candidate inputs; final replay uses inputs only.
"""
import argparse,ctypes as C,hashlib,json,math,os,struct,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from test_runtime import Runner,state
from find_routes import BOSSES

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fight-boss',action='store_true');parser.add_argument('--resume',type=Path,help='Resume a verified input tape by replaying it from boot.');parser.add_argument('--damage-weight',type=float,default=6);parser.add_argument('--steps',type=int,default=400);parser.add_argument('--horizon',type=int,default=32);parser.add_argument('--commit',type=int,default=8);args=parser.parse_args()
 assert args.steps>0 and args.horizon>=args.commit>0
 rom=ROOT/'out/release/rom.bin';plan=json.loads((ROOT/'reports/routes/round1.json').read_text());points=[[112,896]]+[step['position'] for step in plan['path']];defs=json.loads((ROOT/'reports/assets.json').read_text())['actor_definitions'];r=Runner(rom);tape=[];trace=[];begin=time.monotonic();progress=0;outcome='budget'
 def capture_state(runner):
  # SGDK reserves the top STACK_SIZE bytes. Stack scratch contents can
  # differ across otherwise identical cold-boot input replays.
  end=(int.from_bytes(runner.read('heapEnd',4),'big')&65535)+2
  get=runner.lib.m68k_get_reg;get.argtypes=[C.c_int];get.restype=C.c_uint
  return bytes(runner.ram[:end]),end,tuple(get(n) for n in (16,17,18))
 def run(mask):
  r.run(1,mask)
  if tape and tape[-1][0]==mask:tape[-1][1]+=1
  else:tape.append([mask,1])
 if args.resume:
  prior=json.loads(args.resume.read_text());assert prior['tape_verified'] and prior['rom_sha256']==hashlib.sha256(rom.read_bytes()).hexdigest()
  for mask,count in prior['input_tape']:
   for _ in range(count):run(mask)
  trace=prior['trace'];progress=trace[-1]['route_index'] if trace else 0
 else:
  for _ in range(100):run(0)
  for _ in range(2):run(8)
 def keys(base,attack,s):
  return (base&~1)|(1 if base&1 and s.frame%4<2 else 0)|(2 if attack and s.frame%24<8 else 0)
 def route_score(s):
  x,y=s.p.x/256,s.p.y/256
  distance,j=min((math.hypot(x-points[j][0],y-points[j][1]),j) for j in range(max(0,progress-6),min(len(points),progress+25)))
  return j*8-distance*.7,j
 def score(s):
  if s.mode==4 or s.p.hp==0:return -100000
  if s.mode==5 or s.round>0:return 100000
  value,_=route_score(s)
  return value+s.p.hp*250+s.p.armor*90+s.kills*2
 actions=[(d|jump,attack) for jump in (0,1) for d in (0,128,64,16,144,80,32) for attack in (False,True)]
 for iteration in range(args.steps):
  initial=state(r)
  if iteration>=32 and len(trace)>=32 and all(row['route_index']==progress for row in trace[-32:]):outcome='controller_stalled';break
  if initial.mode!=1:outcome={4:'death',5:'round_clear',3:'shop',8:'rescue'}.get(initial.mode,'mode_transition');break
  if not args.fight_boss and any(a.active and (defs[a.definition]['bank'],defs[a.definition]['address'])==BOSSES[0] for a in initial.actors):outcome='boss_spawned';break
  best=None
  # Process copies preserve all core and frontend state, including state omitted
  # by this pinned core's standard savestate interface. Parent never rewinds.
  for batch in range(0,len(actions),4):
   pending=[]
   for base,attack in actions[batch:batch+4]:
    reader,writer=os.pipe();pid=os.fork()
    if pid==0:
     os.close(reader)
     try:
      # Rendering still runs in the emulated VDP; avoid unused frontend images.
      sink=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t)(lambda *unused:None)
      r.lib.retro_set_video_refresh(sink)
      cursor=None;tail_frame=0
      for forecast in range(args.horizon):
       child=state(r)
       if forecast<args.commit:buttons=keys(base,attack,child)
       else:
        if cursor is None:
         _,cursor=route_score(child);cursor=min(cursor,len(plan['path'])-1);tail_frame=child.frame
        if ((child.frame-tail_frame)&65535)>=plan['path'][cursor]['ticks']:
         cursor=min(cursor+1,len(plan['path'])-1);tail_frame=child.frame
        raw=plan['path'][cursor]['input']
        buttons=(128 if raw&1 else 0)|(64 if raw&2 else 0)|(32 if raw&4 else 0)|(16 if raw&8 else 0)|(1 if raw&32 else 0)
        if attack and child.frame%24<8:buttons|=2
       r.run(1,buttons)
       if state(r).mode!=1:break
      end=state(r);value=score(end)
      if end.mode==1:
       for before,after in zip(initial.actors,end.actors):
        if before.active and (not after.active or (before.source,before.definition)==(after.source,after.definition)):
         damage=before.hp-(after.hp if after.active else 0)
         if (defs[before.definition]['bank'],defs[before.definition]['address'])==BOSSES[0]:damage+=(before.life-(after.life if after.active else 0))*32
         value+=max(0,damage)*args.damage_weight
      os.write(writer,struct.pack('d',value))
     except BaseException:
      traceback.print_exc();os._exit(1)
     os._exit(0)
    os.close(writer);pending.append((pid,reader,base,attack))
   for pid,reader,base,attack in pending:
    data=os.read(reader,8);os.close(reader);_,status=os.waitpid(pid,0)
    assert status==0 and len(data)==8,'Candidate process failed'
    value=struct.unpack('d',data)[0]
    if best is None or value>best[0]:best=(value,base,attack)
  for _ in range(args.commit):
   s=state(r);run(keys(best[1],best[2],s))
   if state(r).mode!=1:break
  s=state(r);_,position=route_score(s)
  if math.hypot(s.p.x/256-points[position][0],s.p.y/256-points[position][1])<32:progress=max(progress,position)
  trace.append(dict(step=len(trace),route_index=progress,position=[s.p.x//256,s.p.y//256],mode=s.mode,armor=s.p.armor,hp=s.p.hp,score=round(best[0],2),input=best[1],attack=best[2]))
  if iteration%25==0:print(json.dumps(trace[-1]),flush=True)
 final=bytes(state(r));final_ram,ram_end,cpu=capture_state(r);r.capture('route-search-play.png');r.close()
 verify=Runner(rom)
 for mask,count in tape:verify.run(count,mask)
 replayed=bytes(state(verify));replayed_ram,replayed_end,replayed_cpu=capture_state(verify);verified=replayed==final and replayed_ram==final_ram and (replayed_end,replayed_cpu)==(ram_end,cpu)
 verify.close()
 report=dict(rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),outcome=outcome,tape_verified=verified,persistent_ram_sha256=hashlib.sha256(final_ram).hexdigest(),persistent_ram_end=ram_end,cpu_pc_sr_sp=cpu,expected_state_sha256=hashlib.sha256(final).hexdigest(),replayed_state_sha256=hashlib.sha256(replayed).hexdigest(),settings={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},seconds=round(time.monotonic()-begin,2),video_frames=sum(n for _,n in tape),input_tape=tape,trace=trace,scope='Controller search in forked emulator process copies, followed by exact input-only replay from a fresh title. No game RAM edits. Verification covers static/heap RAM and CPU PC/SR/SP; uninitialized stack contents are excluded. Boss spawn is not boss victory; this is not a complete playthrough.')
 (ROOT/'reports/route-play.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('outcome','tape_verified','video_frames','seconds')}))
 assert verified,'Chosen input tape does not reproduce the explored terminal state'
if __name__=='__main__':main()
