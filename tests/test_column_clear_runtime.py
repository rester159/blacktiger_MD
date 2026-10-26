"""Injected Round 4 column clear entries; native descent and victory rendering."""
import hashlib,json,sys
from test_runtime import ROOT,Runner,state,put


def check(lap,y):
    r=Runner(ROOT/'out/release/rom.bin')
    try:
        r.run(100);r.start_game();r.run(20)
        s=state(r);s.round=3;s.mode=4;s.mode_timer=0;put(r,s);r.run(100)
        s=state(r);s.mode=2;put(r,s);r.run(30)
        x=1016+lap
        s=state(r);s.p.x=x*256;s.p.y=y*256;s.p.climb=1;s.p.vx=s.p.vy=0
        s.cam_x=(x-112)&65535;s.cam_y=0
        for a in s.actors:a.active=0
        for i in range(160):s.spawned[i]=2
        s.mode=1;put(r,s);r.run(4,16)
        assert r.read('player_motion',30)[22], 'fixture must hang from column'
        s=state(r);s.mode=2;put(r,s);r.run(30)
        s=state(r);s.mode=5;r.write('round_clear',0,bytes(8));put(r,s)
        for tick in range(300):
            r.run(1);s=state(r);c=r.read('round_clear',8)
            assert s.p.x//256==x,('player moved horizontally',lap,y)
            assert ((x-s.cam_x)&65535)==112,('camera jumped during column descent',lap,y,s.cam_x)
            if c[1]:break
        else:raise AssertionError('never landed')
        assert tick>3 and s.p.y//256==192,('ground landing',lap,y)
        assert c[5]==112 and c[6]==144,('victory screen position',list(c))
        m=r.read('player_motion',30)
        assert not(m[15] or m[21] or m[22]),'victory before landing'
        r.run(8);r.capture(f'column-clear-{lap}-{y}.png')
        return dict(lap=lap,column_y=y,landing_y=192,screen_x=112,screen_y=144)
    finally:r.close()

if __name__=='__main__':
    pairs=[tuple(map(int,sys.argv[1:]))] if len(sys.argv)>1 else [(lap,y) for lap in (-2048,0,2048) for y in (80,144)]
    result=dict(passed=True,cases=[check(*p) for p in pairs],scope=__doc__,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest())
    (ROOT/'reports/column-clear-runtime-tests.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
