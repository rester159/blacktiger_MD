"""Fixed 7138 breakable pots: placements, round shuffle and animation events."""
import struct
from extract_animation import compile_clip

def extract(s):
    s.expect(None,0x2439,'1110ea012000edb00610')
    s.expect(None,0x714a,'d53a30e93d5f16002110ea197ed60287')
    s.expect(None,0x71e4,'dd35152814')
    tables=[list(s.read(6,s.word(6,0xb718+2*r),32)) for r in range(8)]
    placements=[]
    for r in range(8):
        rows=set()
        for p in struct.unpack('<33H',s.read(5,s.word(None,0x1e07+2*r),66))[1:]:
            for i in range(128):
                raw=s.read(5,p+8*i,8)
                if raw[:2]==b'\xff\xff':break
                x,y,pc,bank,persistent=struct.unpack('<HHHBB',raw)
                if bank>7 or pc<0x100 or pc>=0xc000:break
                if pc==0x7138:
                    assert 1<=persistent<=32
                    rows.add((x,y,persistent-1))
        placements.append(sorted(rows))
    segments=[];indices={};pending=[]
    def intern(pc):
        if pc not in indices:
            indices[pc]=len(segments);segments.append(None);pending.append(pc)
        return indices[pc]
    roots=[]
    for kind in range(2,16):
        closed=s.read(None,s.word(None,0x730b+2*(kind-2)),32)
        opened=s.read(None,s.word(None,0x74c7+2*(kind-2)),32)
        roots.append([intern(int.from_bytes(closed[30:32],'little')+5),intern(int.from_bytes(opened[30:32],'little')+5),intern(s.word(None,0x772f+2*(kind-2)))])
    puff=intern(0x79e5);cracked=intern(0x76bb)
    while pending:
        pc=pending.pop(0);clip=compile_clip(s,None,pc);event=0;nxt=65535
        if clip['event']:
            e=clip['event'];assert e['address'],hex(pc);event={0x71e4:1,0x7222:2,0x7251:3,0x7261:4,0x72aa:5}[e['address']]
            if event in (4,5):nxt=intern(e['record']+3)
        segments[indices[pc]]=dict(clip=clip,event=event,next=nxt)
    return dict(tables=tables,placements=placements,roots=roots,puff=puff,cracked=cracked,segments=segments,score=int(''.join(map(str,s.read(None,0x15bd,8)))),witnesses=list(s.witnesses.values()))
