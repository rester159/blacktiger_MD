#!/usr/bin/env python3
"""Offline arcade-data to native Genesis conversion. No arcade code is shipped.
Requires supplied ROM set; all input files are checked against its SHA256 lock.
"""
import argparse, hashlib, json, struct, shutil
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'_capcom/black tiger'
DEFAULT=OLD/'assets/source_packages/arcade/blktiger_supplied_romset_e54221c17ce6b5ee'
OUT=ROOT/'res/generated'
def sha(b):return hashlib.sha256(b).hexdigest()
def words(v):return struct.pack('>'+str(len(v))+'H',*map(int,v))
def rgb(w):return ((w>>1)&7,(w>>5)&7,(w>>9)&7)
COL=np.array([rgb((i&7)*2+((i>>3)&7)*32+(i>>6)*512) for i in range(512)],dtype=np.int32)
def colid(w):return ((w>>1)&7)|(((w>>5)&7)<<3)|(((w>>9)&7)<<6)
def quant(hist):
    ids=np.flatnonzero(hist); x=COL[ids]; w=hist[ids]
    centers=[np.array([0,0,0]),np.array([7,7,7])]
    for _ in range(13):
        d=((x[:,None,:]-np.array(centers)[None,:,:])**2).sum(2).min(1)
        centers.append(x[np.argmax(d*np.sqrt(w))])
    c=np.array(centers)
    for _ in range(20):
        ix=((x[:,None,:]-c[None,:,:])**2).sum(2).argmin(1); n=c.copy()
        for j in range(2,15):
            m=ix==j
            if m.any():n[j]=np.rint((x[m]*w[m,None]).sum(0)/w[m].sum()).astype(int)
        if np.array_equal(c,n):break
        c=n
    return c

def decode(region,lay):
    data=np.frombuffer(region,dtype=np.uint8); count=len(region)*8//(lay['item_increment_bits']*len(lay['plane_offsets_bits']))
    # Fractional layouts address two independent halves: physical count is 2048.
    count=2048
    base=np.arange(count)[:,None,None]*lay['item_increment_bits']+np.array(lay['y_offsets_bits'])[None,:,None]+np.array(lay['x_offsets_bits'])[None,None,:]
    pen=np.zeros(base.shape,dtype=np.uint8)
    for plane in lay['plane_offsets_bits']:
        bit=base+plane; pen=(pen<<1)|((data[bit//8]>>(7-bit%8))&1)
    return pen

def pack(a):
    a=np.asarray(a,dtype=np.uint8).reshape(-1)
    return ((a[::2]<<4)|a[1::2]).tobytes()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=DEFAULT);args=ap.parse_args()
    lock=json.loads((args.source/'source_lock.json').read_text());files={}
    for r in lock['files']:
        b=(args.source/'payload'/r['path']).read_bytes();assert len(b)==r['size'] and sha(b)==r['sha256'];files[r['path']]=b
    board=json.loads((ROOT/'assets/board.json').read_text())
    def read(bank,pc,n):
        if pc<0x8000:return files['bdu-01a.5e'][pc:pc+n]
        name=('bdu-02a.6e','bdu-03a.8e','bd-04.9e','bd-05.10e')[bank//4];at=(bank%4)*0x4000+pc-0x8000
        assert 0<=at and at+n<=len(files[name]);return files[name][at:at+n]
    def u16(b,p=0):return int.from_bytes(b[p:p+2],'little')
    def pal(round):
        mem=bytearray(0x800); ptr=u16(read(6,0x8136+round*2,2))
        for _ in range(20):
            b=read(6,ptr,6)
            if b[:2]==b'\xff\xff':break
            start,dest,count=struct.unpack('<HHH',b);assert 0xd800<=dest<0xe000 and count<0x401
            mem[dest-0xd800:dest-0xd800+count]=read(6,start,count);ptr+=6
        p=u16(read(0,0x1acf,2));overlay=read(0,p,20)
        mem[0x200:0x20a]=overlay[:10];mem[0x600:0x60a]=overlay[10:]
        return [((mem[i]>>5)<<1)|(((mem[i]&15)>>1)<<5)|(((mem[0x400+i]&15)>>1)<<9) for i in range(0x400)]
    OUT.mkdir(parents=True,exist_ok=True);(ROOT/'reports').mkdir(exist_ok=True)
    tiles=decode(b''.join(files[r['path']] for r in board['regions']['tiles']['files']),board['layouts']['tiles'])
    sprites=decode(b''.join(files[r['path']] for r in board['regions']['sprites']['files']),board['layouts']['sprites'])
    resources=[];decl=[];body=[];report={'source':lock,'rounds':[],'unresolved_spawn_rows':[],'adaptations':['Two 15-color background palettes; one exact RGB333 hero palette; one shared 15-color object palette.','Background priority groups are flattened.','Actor behavior families are native approximations pending arcade comparison.']}
    def emit(name,b,typ='u16'):
        (OUT/(name+'.bin')).write_bytes(b);resources.append(f'BIN {name} "generated/{name}.bin" 4');decl.append(f'extern const {typ} {name}[];')
    p0=pal(0);scols=np.array([rgb(w) for w in p0[512:640]])
    hist=np.zeros(512,dtype=np.int64)
    for p in range(1,8):
        for k in range(15):hist[colid(p0[512+p*16+k])]+=1
    enemy=quant(hist);enemy=enemy[[0,*range(2,15),1]]; hero=np.array([rgb(w) for w in p0[512:527]])
    cram=[0]+[int(c[0]*2+c[1]*32+c[2]*512) for c in hero]+[0]+[int(c[0]*2+c[1]*32+c[2]*512) for c in enemy]
    emit('object_palette',words(cram))
    smap=[]
    for p in range(8):
        smap.append(list(range(1,16))+[0] if p==0 else [int(((enemy-c)**2).sum(1).argmin())+1 for c in scols[p*16:p*16+15]]+[0])
    # ROM sprite atlas, hardware column-major tile order. All eight palette variants.
    atlas=bytearray()
    for p in range(8):
        pp=np.array(smap[p],dtype=np.uint8)[sprites]
        for a in pp:
            for x,y in ((0,0),(0,8),(8,0),(8,8)):atlas.extend(pack(a[y:y+8,x:x+8]))
    emit('object_patterns',bytes(atlas),'u32')
    sheet=Image.new('RGB',(512,1024))
    for i,a in enumerate(sprites):
        color=np.vstack(([20,20,28],np.array(hero)*255//7))
        pixels=color[np.array(smap[0])[a]].astype(np.uint8)
        sheet.paste(Image.fromarray(pixels),(i%32*16,i//32*16))
    sheet.save(ROOT/'reports/sprites.png')
    # Four body pieces and weapon per hero frame, with each ROM-owned flip/offset.
    poses=[]
    for pose in range(10):
        table=u16(read(7,0x9120+2*pose,2));frames=[]
        for face in (0,4):
            first=u16(read(7,table+2*face,2))
            for frame in range(8):
                raw=read(7,first+6*frame,6)
                base,attr,weapon,wa,dx,dy=raw; flip=(attr>>3)&1
                codes=[base,base+1,base+8,base+9]
                if flip:codes=[base+1,base,base+9,base+8]
                frames.append('{{'+','.join(map(str,[*[c|((attr&0xe0)<<3) for c in codes],weapon|((wa&0xe0)<<3)]))+'},'+','.join(map(str,[flip,(wa>>3)&1,dx if dx<128 else dx-256,dy if dy<128 else dy-256]))+'}')
        poses.append('{'+','.join(frames)+'}')
    body.append('const HeroFrame hero_frames[10][16]={'+',\n'.join(poses)+'};')
    # Constructors identified by bank/address. Keep identity only in conversion report.
    # Families: walker, flyer, turret, falling rock, hazard, chest, captive, pickup, boss.
    family={(0,0x93ed):0,(0,0x8000):0,(0,0x8389):0,(0,0x89c6):1,(0,0x9b85):1,(0,0xa35c):0,
      (0,0xab33):6,(0,0xab4a):6,(0,0xb84f):2,(1,0xb2a9):4,(1,0xacbe):3,(1,0xacd3):3,
      (2,0xacac):5,(2,0xb67f):2,(2,0x8000):0,(2,0x8344):0,(3,0xaab3):0,(4,0xb338):1,
      (4,0xb4af):7,(4,0xb515):7,(2,0xa6f8):2,(1,0x8a03):1,(1,0x8a5d):1,(1,0x8d33):1}
    defs={};spawns=[]
    for r in range(8):
        root=u16(read(0,0x1e07+2*r,2));ptrs=struct.unpack('<33H',read(5,root,66));rows={}
        for cell,p in enumerate(ptrs[1:],1):
            for index in range(128):
                raw=read(5,p,8)
                if raw[:2]==b'\xff\xff':break
                x,y,pc,b,k=struct.unpack('<HHHBB',raw)
                if b>7 or pc<0x100 or pc>=0xc000:
                    report['unresolved_spawn_rows'].append({'round':r+1,'cell':cell,'address':p,'bytes':raw.hex()});break
                p+=8
                if pc in (0x7138,0x6f71):continue # scanner control / hidden item: separate semantics not guessed
                key=(b if pc>=0x8000 else 0,pc)
                if key not in defs:
                    block=read(key[0],pc,min(180,0xc000-pc))
                    template=None
                    for j in range(len(block)-9):
                        if block[j]==0x21 and block[j+3:j+4]==b'\x01' and block[j+4] in (32,48,64) and block[j+5:j+8]==b'\x00\xed\xb0':
                            a=u16(block,j+1)
                            if 0x100<=a<0xbfd0:template=read(key[0],a,32);break
                    kind=family.get(key,0);code=0x280;attr=0x45;frames=1;hp=3
                    if template:
                        hp=max(1,min(32,template[0x10]));aptr=u16(template,30)
                        if 0x100<=aptr<0xbff0:
                            anim=read(key[0],aptr,32)
                            # Animation cursors point BEFORE the first record. Tables
                            # use 5 or 8-byte rows, independently of object size.
                            candidates=[]
                            for off in (5,8):
                                if 1<=anim[off]<=200 and anim[off+2]&7<8:
                                    score=0
                                    stride=8 if anim[off+5:off+6]==b'\x00' and 0x100<=u16(anim,off+6)<0xc000 else 5
                                    if anim[off+stride] in (0,255) or 1<=anim[off+stride]<=200:score+=1
                                    if template[12]==11 and off==5:score+=2
                                    if template[12]==9 and off==5:score+=2
                                    # First duration is most often 4/8/16/40/200.
                                    if anim[off] in (1,2,4,6,8,16,24,32,40,64,200):score+=2
                                    if anim[off+2]&0x10:score-=4
                                    candidates.append((score,-off,off))
                            if candidates:
                                off=max(candidates)[2];code=anim[off+1]|((anim[off+2]&0xe0)<<3);attr=anim[off+2]
                    if 0x5e32<=pc<=0x5eb0:kind=7;code=0x20+(pc-0x5e32)//18;attr=0x03
                    if key in ((2,0x8ef4),(3,0x8000),(3,0x991d),(3,0x9b24),(3,0xb7f3),(0,0xb1c1),(4,0x9eb1),(4,0x9f16)):kind=8;hp=48+r*8
                    if key==(0,0x93ed):code=0x280;attr=0x45;frames=3
                    if key==(0,0x8000):code=0x240;attr=0x42;frames=3
                    if key==(2,0x8000):code=0x3c0;attr=0x63;frames=3
                    size=1 if kind in (4,7) else 4
                    defs[key]={'id':len(defs),'bank':key[0],'address':pc,'kind':kind,'code':code,'palette':attr&7,'hp':hp,'pieces':size,'frames':frames,'behavior_verified':False}
                rows[(x,y,k)]=(x,y,defs[key]['id'],k)
        spawns.append(sorted(rows.values()))
    ds=[]
    for d in defs.values():ds.append('{'+','.join(map(str,[d['code'],d['kind'],d['palette'],d['hp'],d['pieces'],d['frames']]))+'}')
    body.append('const ActorDef actor_defs[]={'+','.join(ds)+'};');report['actor_definitions']=list(defs.values())
    collision=files['bdu-03a.8e'][0x363a:0x3e3a]
    for r in range(8):
        cfg=read(6,0xb19c+r*6,6);cx,cy,layout,_=struct.unpack('<HHBB',cfg);w,h=(128,64) if layout else (64,128)
        raw=read(8+r,0x8000,16384);colors=pal(r);hist=np.zeros((16,512),dtype=np.int64)
        for i in range(0,16384,2):
            a,b=raw[i:i+2];code=a+((b&7)<<8);p=(b>>3)&15
            freq=np.bincount(tiles[code].flatten(),minlength=16)
            for k,n in enumerate(freq):hist[p,colid(colors[p*16+k])]+=int(n)
        groups=np.array([0]*8+[1]*8)
        for _ in range(5):
            cp=[quant(hist[groups==g].sum(0)) for g in range(2)]
            cost=np.array([((COL[:,None,:]-c[None,:,:])**2).sum(2).min(1) for c in cp])
            groups=(hist@cost.T).argmin(1)
        cp=[quant(hist[groups==g].sum(0)) for g in range(2)]
        palettes=[];pm=[]
        for c in cp:palettes += [0]+[int(v[0]*2+v[1]*32+v[2]*512) for v in c]
        for p in range(16):pm.append([int(((cp[groups[p]]-rgb(c))**2).sum(1).argmin())+1 for c in colors[p*16:p*16+16]])
        pats=bytearray();unique={};world=[];coll=[];preview=Image.new('RGB',(w*16,h*16))
        for y in range(h):
            for x in range(w):
                idx=(x&15)|((y&15)<<4)|((x&(0x70 if layout else 0x30))<<4)|((y&(0x30 if layout else 0x70))<<(7 if layout else 6))
                lo,attr=raw[idx*2:idx*2+2];code=lo+((attr&7)<<8);p=(attr>>3)&15;flip=bool(attr&128)
                coll.append(collision[code]);pix=np.array(pm[p],dtype=np.uint8)[tiles[code]]
                if flip:pix=pix[:,::-1]
                pp=np.array([[0,0,0]]+list(cp[groups[p]]))*255//7
                preview.paste(Image.fromarray(pp[pix].astype(np.uint8)),(x*16,y*16))
                ws=[]
                for oy,ox in ((0,0),(0,8),(8,0),(8,8)):
                    cell=pix[oy:oy+8,ox:ox+8]
                    b,flags=min((pack(cell),0),(pack(cell[:,::-1]),0x800),(pack(cell[::-1,:]),0x1000),(pack(cell[::-1,::-1]),0x1800))
                    if b not in unique:unique[b]=len(unique);pats.extend(b)
                    ws.append((unique[b]+16)|(int(groups[p])<<13)|flags)
                world.append(ws)
        # Row-major 8x8 map enables contiguous strip uploads; only the entering edges stream.
        wm=[]
        for y in range(h*2):
            for x in range(w*2):wm.append(world[(y//2)*w+x//2][(y&1)*2+(x&1)])
        assert len(unique)<1700,(r,len(unique))
        emit(f'bg{r}',bytes(pats),'u32');emit(f'map{r}',words(wm));emit(f'pal{r}',words(palettes));emit(f'collision{r}',bytes(coll),'u8')
        spawn=spawns[r];body.append(f'const Spawn spawn{r}[]={{'+','.join('{'+','.join(map(str,s))+'}' for s in spawn)+'};')
        preview.resize((w*8,h*8)).save(ROOT/f'reports/round{r+1}.png')
        report['rounds'].append({'round':r+1,'width':w*16,'height':h*16,'camera':[cx,cy],'layout':layout,'patterns':len(unique),'spawns':len(spawn),'collision_codes':dict(Counter(coll))})
    body.append('const Round rounds[8]={'+',\n'.join('{bg%d,map%d,pal%d,collision%d,spawn%d,%d,%d,%d,%d,%d,%d}'%(r,r,r,r,r,d['patterns'],d['spawns'],d['width'],d['height'],*d['camera']) for r,d in enumerate(report['rounds']))+'};')
    (ROOT/'res/assets.res').write_text('\n'.join(resources)+'\n')
    (ROOT/'inc/assets.h').write_text('#ifndef ASSETS_H\n#define ASSETS_H\n#include "game.h"\n'+'\n'.join(decl)+'\nextern const HeroFrame hero_frames[10][16];\nextern const ActorDef actor_defs[];\nextern const Round rounds[8];\n#endif\n')
    (ROOT/'src/data.c').write_text('/* Generated by tools/extract.py. */\n#include <genesis.h>\n#include "assets.h"\n'+'\n'.join(body)+'\n')
    report['outputs']={p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in OUT.glob('*.bin')}
    (ROOT/'reports/assets.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['rounds'],indent=2));print('native asset bytes',sum(p.stat().st_size for p in OUT.glob('*.bin')))
if __name__=='__main__':main()
