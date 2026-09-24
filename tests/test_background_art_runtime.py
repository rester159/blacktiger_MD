"""All-eight-level palette, scrolling/cache and repeating-art regression review."""
import ctypes as C, hashlib, json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from profile_encounters import locations, setup
from test_runtime import ROOT, state, put, check_video_cache
THEMES=('Ruins','Caverns','Catacombs','Cave','Mountains','Sky temple','Stained glass','Palace')
rom=ROOT/'out/release/rom.bin';checks=[];shots=[];cases=locations()
for level in range(8):
    choices=[c for c in cases if c['level']==level];case=choices[len(choices)//2]
    r=setup(case,rom,None);r.run(60)
    shot=Image.fromarray(r.frame.copy());shot.save(ROOT/f'reports/art-review-level{level+1}-v25.png');shots.append(shot)
    expected=np.fromfile(ROOT/f'res/generated/pal{level}.bin',dtype='>u2')
    expected=[((int(c)>>1)&7)|(((int(c)>>5)&7)<<3)|(((int(c)>>9)&7)<<6) for c in expected]
    cram=(C.c_uint16*64).in_dll(r.lib,'cram')
    assert list(cram)[:32]==expected,(level,'scenery palette not installed')
    s=state(r);s.mode=2
    for a in s.actors:a.active=0
    for q in s.shots:q.active=0
    s.p.x=s.p.y=-1024*256;put(r,s);r.run(30)
    for x,y in ((0,0),(7,8),(255,128),(511,400),(512,560),(767,784),(1023,400),(1536,128)):
        s=state(r);s.cam_x=x;s.cam_y=y;put(r,s);r.run(40);check_video_cache(r,state(r))
    assert int.from_bytes(r.read('video_cache_faults'),'big')==0
    assert int.from_bytes(r.read('vblank_flush_overruns'),'big')==0
    checks.append(dict(level=level+1,theme=THEMES[level],palette_installed=True,camera_positions=8,cache_faults=0,vblank_overruns=0))
    r.close()
# The exported native-art previews have matching outer colors, not a cropped
# architecture fragment. This guards both horizontal and vertical repeats.
for level in (5,7):
    pixels=np.array(Image.open(ROOT/f'reports/backdrop-level{level}-tiles.png'))
    assert np.array_equal(pixels[:,0],pixels[:,-1]),(level,'horizontal seam')
    assert np.array_equal(pixels[0],pixels[-1]),(level,'vertical seam')
    assert len(np.unique(pixels.reshape(-1,3),axis=0))>=3,(level,'empty art')
sheet=Image.new('RGB',(1024,480));draw=ImageDraw.Draw(sheet)
for i,shot in enumerate(shots):
    x=(i%4)*256;y=(i//4)*240;sheet.paste(shot,(x,y+16));draw.text((x+4,y+2),f'{i+1}  {THEMES[i]}',fill='white')
sheet.save(ROOT/'reports/art-review-v25.png')
report=dict(passed=True,rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),checks=checks,seam_levels=[5,7],scope='Eight sampled camera positions per level, native palette/VRAM checks, compiled repeating scenery edges and representative screenshots. Not a full-level playthrough or proof of artistic quality.')
(ROOT/'reports/background-art-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
