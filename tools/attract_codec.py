"""Small streaming LZSS codec for native presentation events (4 KiB window)."""
from collections import defaultdict, deque

def pack(data):
    data=bytes(data);chains=defaultdict(deque);out=bytearray();at=0
    while at<len(data):
        flag_at=len(out);out.append(0);flags=0
        for bit in range(8):
            if at==len(data):break
            key=data[at:at+3];q=chains[key]
            while q and at-q[0]>4096:q.popleft()
            best=0;distance=0
            for pos in reversed(q):
                n=3
                while n<18 and at+n<len(data) and data[pos+n]==data[at+n]:n+=1
                if n>best:best=n;distance=at-pos
                if best==18:break
            if best>=3:
                d=distance-1;out.extend((d>>4,((d&15)<<4)|(best-3)));n=best
            else:
                flags|=1<<bit;out.append(data[at]);n=1
            for p in range(at,at+n):
                k=data[p:p+3];c=chains[k]
                while c and p-c[0]>4096:c.popleft()
                c.append(p)
            at+=n
        out[flag_at]=flags
    return bytes(out)

def unpack(data,size):
    out=bytearray();at=0
    while len(out)<size:
        flags=data[at];at+=1
        for bit in range(8):
            if len(out)==size:break
            if flags&(1<<bit):out.append(data[at]);at+=1
            else:
                a,b=data[at:at+2];at+=2;d=((a<<4)|(b>>4))+1
                for _ in range((b&15)+3):out.append(out[-d])
    assert at==len(data)
    return bytes(out)
