"""Capture native backgrounds with actors and HUD hidden for visual review."""
import ctypes as C,sys
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from profile_encounters import setup,locations
from test_runtime import ROOT,state,put,check_video_cache
cases=locations();shots=[]
for level in range(8):
 choices=[c for c in cases if c['level']==level];r=setup(choices[len(choices)//2],ROOT/'out/release/rom.bin',None)
 s=state(r);s.mode=2;s.p.x=s.p.y=-1024*256
 for a in s.actors:a.active=0
 for q in s.shots:q.active=0
 if level==3:s.cam_x=48;s.cam_y=784
 if level==4:s.cam_x=640;s.cam_y=768
 if level==5:s.cam_x=160;s.cam_y=208
 put(r,s);r.run(80);check_video_cache(r,state(r))
 v=(C.c_uint8*65536).in_dll(r.lib,'vram')
 # Preserve the far-plane rows; clear only HUD/menu name-table rows.
 for row in (*range(5),25,26,27):
  for i in range(64):v[(0xc000+row*128+i)^1]=0
 # Restore the source name-table cells covered by the PAUSED label.
 rom=(ROOT/'out/release/rom.bin').read_bytes()
 for col in range(13,19):
  x=(col+s.cam_x//16)&63 if level in (3,4,6,7) else col
  if level in (3,4,6):
   at=r.symbols[f'backdrop_{level}_map']+((12-5)*64+x)*2
   word=int.from_bytes(rom[at:at+2],'big')
  elif level==7:
   at=r.symbols['arena_far']+((12-5)*16+(x&15))*2
   word=int.from_bytes(rom[at:at+2],'big')
  else:word=0
  at=0xc000+12*128+x*2;v[at^1]=word>>8;v[(at+1)^1]=word&255
 r.run(3)
 shot=Image.fromarray(r.frame.copy());shot.save(ROOT/f'reports/background-level{level+1}-v26.png');shots.append(shot);r.close()
# Compact 4 by 2 layout at native scale, with no interpolation.
sheet=Image.new('RGB',(1024,480),(14,14,18));d=ImageDraw.Draw(sheet)
for i,shot in enumerate(shots):
 x=i%4*256;y=i//4*240;sheet.paste(shot,(x,y+16));d.text((x+4,y+2),f'LEVEL {i+1}',fill='white')
sheet.save(ROOT/'reports/backgrounds-all-eight-v26.png')
print('Captured all eight native backgrounds using existing game art.')
