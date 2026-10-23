"""Dormant boss damage and wrapped first arrivals, not a full level playthrough."""
import hashlib,json
from test_skeleton_runtime import ROOT,Runner,state,put,fixture


def dormant_damage(constructor, rush=False):
    r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(20)
    try:
        slot,row,level=fixture(r,0,1,constructor,approach=160,vertical=32)
        if rush:
            r.write('boss_rush',0,bytes([1,4 if constructor==0x98a3 else 6,0,0]))
            s=state(r);s.round=7;s.mode=4;s.mode_timer=0;put(r,s);r.run(100)
            s=state(r);s.mode=2;put(r,s);r.run(20);slot=0
        s=state(r);a=s.actors[slot]
        assert r.read('wavebosses',16*24)[slot*16+14]==0
        # Controlled head projectile before proximity activation. The ordinary
        # collision dispatcher and native damage/activation scripts run next.
        q=s.shots[0];q.active=1;q.life=30;q.damage=254;q.kind=1
        q.x=a.x+24*256;q.y=a.y-4*256;s.mode=1;s.p.invincible=10000
        put(r,s);r.run(120);s=state(r)
        assert r.read('wavebosses',16*24)[slot*16+14]==1
        assert s.actors[slot].state==0,('activated boss remains hit-locked',level+1)
        initial=s.actors[slot].life
        # Actual head contacts must consume all remaining layers and clear.
        for _ in range(2400):
            s=state(r)
            if s.mode==(3 if rush else 5):break
            a=s.actors[slot];q=s.shots[0]
            q.active=1;q.life=2;q.damage=254;q.kind=1;q.x=a.x+24*256;q.y=a.y-4*256
            s.p.invincible=10000;put(r,s);r.run(1)
        else:raise AssertionError(('boss cannot be defeated after early damage',level+1))
        return dict(round=level+1,boss_rush=rush,layers=initial,early_damage=True,clear=True)
    finally:r.close()


def wrapped_arrival(lap):
    r=Runner(ROOT/'out/release/rom.bin');r.run(100);r.start_game();r.run(20)
    try:
        s=state(r);s.round=2;s.mode=4;s.mode_timer=0;put(r,s);r.run(100)
        s=state(r);s.mode=2;put(r,s);r.run(20)
        s=state(r);s.p.x=(880+lap)*256;s.p.y=1568*256
        s.p.vx=s.p.vy=0;s.p.invincible=10000
        s.cam_x=(768+lap)&65535;s.cam_y=1424;put(r,s);r.run(20)
        s=state(r);s.mode=1;put(r,s)
        previous=880+lap
        for _ in range(120):
            r.run(1);s=state(r)
            assert abs(s.p.x//256-previous)<=4,('arena teleported player',lap,previous,s.p.x//256)
            previous=s.p.x//256
        boss=next(a for a in s.actors if a.active and a.source==79)
        cx=(s.cam_x+32768)%65536-32768
        assert boss.x//256+128>cx and boss.x//256<cx+256,('dragon outside view',lap)
        r.capture(f'round3-first-arrival-{lap}.png')
        return dict(lap=lap,player_x=s.p.x//256,boss_x=boss.x//256,visible=True)
    finally:r.close()


if __name__=='__main__':
    result=dict(passed=True,dormant_damage=[dormant_damage(c,rush) for rush in (False,True) for c in (0x98a3,0x98e8)],
                wrapped_arrivals=[wrapped_arrival(lap) for lap in (-1024,0,1024)],
                rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),scope=__doc__)
    (ROOT/'reports/boss-first-contact-runtime-tests.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
