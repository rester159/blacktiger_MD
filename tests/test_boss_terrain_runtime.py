"""Native boss spawning applies source terrain; check resident and streamed VRAM."""
import ctypes as C
import hashlib,json,struct
from test_runtime import ROOT,Runner,state,put

rom=(ROOT/'out/release/rom.bin').read_bytes()
checks=[]
def verify(r,level):
    width=64 if level==2 else 128
    ptr,count=struct.unpack_from('>IH',rom,r.symbols['boss_terrain']+level*6)
    patterns=(ROOT/f'res/generated/{"backdrop_bg" if level==4 else "bg"}{level}.bin').read_bytes()
    remap=None
    if level==4:
        raw=(ROOT/f'res/generated/backdrop_remap{level}.bin').read_bytes();n=len(raw)//4
        remap=struct.unpack('>'+str(n*2)+'H',raw)
    v=(C.c_uint8*65536).in_dll(r.lib,'vram')
    s=state(r);checked=0
    for i in range(count):
        cell,*words=struct.unpack_from('>5H',rom,ptr+i*12)
        y,x=divmod(cell,width)
        for dy in range(2):
            for dx in range(2):
                xx=x*2+dx;yy=y*2+dy
                if not(s.cam_x//8<=xx<s.cam_x//8+33 and s.cam_y//8<=yy<s.cam_y//8+29):continue
                expected=words[dy*2+dx]
                if remap is not None:expected=(expected&0xf800)|0x8000|remap[((expected>>13)&1)*n+(expected&2047)]
                at=0xe000+((yy&31)*64+(xx&63))*2
                actual=(v[at^1]<<8)|v[(at+1)^1]
                assert actual&0xf800==expected&0xf800,(level,cell,'attributes',hex(actual),hex(expected))
                tile=(expected&2047)-16;physical=actual&2047
                assert bytes(v[(physical*32+k)^1] for k in range(32))==patterns[tile*32:tile*32+32],(level,cell,'pixels')
                checked+=1
    assert checked==count*4,(level,checked,count)
    assert r.read('video_cache_faults')==b'\0\0'
    return checked

for level,row,camera_x,camera_y in [(2,79,576,1472),(4,65,1184,0)]:
    r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game(exploration=True);r.run(30)
    s=state(r);s.mode=2;put(r,s);r.run(30)
    s=state(r);s.round=level;s.mode=4;s.mode_timer=0;put(r,s);r.run(100)
    s=state(r);s.mode=2;put(r,s);r.run(30)
    s=state(r);assert s.round==level
    for a in s.actors:a.active=0
    for q in s.shots:q.active=0
    for i in range(160):s.spawned[i]=2
    s.spawned[row]=0;s.cam_x=camera_x;s.cam_y=camera_y
    s.p.x=(camera_x+112)*256;s.p.y=(camera_y+96)*256;s.p.vx=s.p.vy=0
    s.p.invincible=10000;put(r,s);r.run(30)
    assert not r.read('world_opened',1)[0]&128
    s=state(r);s.mode=1;s.previous_input=0;put(r,s)
    for _ in range(30):
        r.run(1)
        if r.read('world_opened',1)[0]&128:break
    else:raise AssertionError(('native boss spawn failed',level))
    s=state(r);assert any(a.active and a.source==row for a in s.actors)
    s.mode=2;put(r,s);r.run(30)
    # Stage 3 patches were already resident; stage 5 entrance closes behind
    # the camera. Inspect it after streaming that region into the viewport.
    s=state(r);s.cam_x=576 if level==2 else 1088;s.cam_y=1472 if level==2 else 0;put(r,s);r.run(30)
    checked=verify(r,level)
    # Stream out and back, then verify the same source patterns again.
    s=state(r);s.cam_x+=320;put(r,s);r.run(30)
    s=state(r);s.cam_x-=320;put(r,s);r.run(30);verify(r,level)
    s=state(r);s.mode=4;s.mode_timer=0;s.p.lives=3;put(r,s);r.run(100)
    assert not r.read('world_opened',1)[0]&128,('closure survived death',level)
    checks.append(dict(round=level+1,tiles=checked,native_boss_spawn=True,reloaded_tiles=True,death_reset=True))
    r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256(rom).hexdigest(),checks=checks,scope='Paused scene setup; native source boss spawning and terrain updates, VRAM attributes and pattern bytes, streaming and death reset. Not a complete playthrough.')
(ROOT/'reports/boss-terrain-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
