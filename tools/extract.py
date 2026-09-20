#!/usr/bin/env python3
"""Offline arcade-data to native Genesis conversion. No arcade code is shipped.
Requires supplied ROM set; all input files are checked against its SHA256 lock.
"""
import argparse, hashlib, json, struct, shutil
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw
from arcade_source import Source
from extract_pair import extract as extract_pair
from extract_boulder import extract as extract_boulder
from extract_boss_motion import extract as extract_boss_motion
from extract_boss import extract as extract_boss
from extract_flailer import extract as extract_flailer
from extract_waveboss import extract as extract_waveboss
from extract_eruption import extract as extract_eruption
from extract_teleporter import extract as extract_teleporter
from extract_hunter import extract as extract_hunter
from extract_reinforcement_body import extract as extract_reinforcement_body
from extract_crawler import extract as extract_crawler
from extract_statue import extract as extract_statue
from extract_checkpoint import extract as extract_checkpoint
from extract_progress import extract as extract_progress
from extract_shop import extract as extract_shop
from extract_container import extract as extract_container
from extract_spitter import extract as extract_spitter
from extract_thrower import extract as extract_thrower
from extract_zombie import extract as extract_zombie
from extract_wisp import extract as extract_wisp
from extract_emerge import extract as extract_emerge
from extract_pickup import extract as extract_pickup
from extract_hazard import extract as extract_hazard
from extract_sentry import extract as extract_sentry
from extract_loot import extract as extract_loot
from extract_skeleton import extract as extract_skeleton
from extract_hidden import extract as extract_hidden
from actor_contract import load as load_actor_contract
from extract_animation import extract as extract_animation
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
    # Proven shared NPC clips are compiled into native frame structs.
    animation=extract_animation(Source(args.source))
    (ROOT/'reference/animation.json').write_text(json.dumps(animation,indent=2)+'\n')
    report['npc_source_contract']=animation['npc']
    def native_clip(name,frames,loop=None):
        rows=[]
        for f in frames:
            hold=(1 if f['vx'] is None else 0)|(2 if f['vy'] is None else 0)
            rows.append('{'+','.join(map(str,[f['code'],f['duration'],f['palette'],int(f['flip']),hold,f['vx'] or 0,f['vy'] or 0]))+'}')
        body.append('static const AnimFrame '+name+'_frames[]={'+(','.join(rows) if rows else '{0}')+'};')
        body.append('const AnimClip '+name+'={'+name+'_frames,'+str(len(rows))+','+str(65535 if loop is None else loop)+'};')
    for name in ('idle','released'):
        clip=animation['npc'][name];native_clip('npc_'+name,clip['frames'],clip['loop'])
    native_clip('npc_rescue',[{'code':f['code'],'duration':f['ticks'],'palette':4,'flip':False,'vx':0,'vy':0} for f in animation['npc']['rescue_cutscene'] if 'code' in f])
    hidden=extract_hidden(Source(args.source))
    (ROOT/'reference/hidden.json').write_text(json.dumps(hidden,indent=2)+'\n')
    for k in hidden['kinds']:
        native_clip('hidden_'+str(k['kind']),k['clip']['frames'],k['clip']['loop'])
    for key in ('life_collected','explosion'):
        native_clip('hidden_'+key,hidden[key]['frames'],hidden[key]['loop'])
    body.append('const AnimClip *const hidden_clips[]={'+','.join('&hidden_'+str(i) for i in range(12))+'};')
    skeleton=extract_skeleton(Source(args.source))
    (ROOT/'reference/skeleton.json').write_text(json.dumps(skeleton,indent=2)+'\n')
    for i,seg in enumerate(skeleton['segments']):
        clip=seg['clip'];native_clip('skeleton_'+str(i),clip['frames'],clip['loop'])
    body.append('const SkeletonSegment skeleton_segments[]={'+','.join('{&skeleton_%d,%d,%d}'%(i,seg['next'],seg['event']) for i,seg in enumerate(skeleton['segments']))+'};')
    body.append('const SkeletonProfile skeleton_profiles[]={'+','.join('{{'+','.join(map(str,p['roots']))+'},'+','.join(map(str,[p['durability'],p['guard'],p['variant'],p['score'],p['weapon_damage'],p['weapon_width'],p['weapon_height'],p['weapon_contact']]))+'}' for p in skeleton['profiles'])+'};')
    flailer=extract_flailer(Source(args.source))
    (ROOT/'reference/flailer.json').write_text(json.dumps(flailer,indent=2)+'\n')
    for i,seg in enumerate(flailer['segments']):native_clip('flailer_'+str(i),seg['clip']['frames'],seg['clip']['loop'])
    body.append('const AnimSegment flailer_segments[]={'+','.join('{&flailer_%d,%d,%d}'%(i,seg['next'],seg['event']) for i,seg in enumerate(flailer['segments']))+'};')
    body.append('const u16 flailer_roots[2][21]={'+','.join('{'+','.join(map(str,r))+'}' for r in flailer['roots'])+'},flailer_scores[]={'+','.join(map(str,flailer['scores']))+'};')
    body.append('const u8 flailer_health[]={'+','.join(map(str,flailer['health']))+'};')
    waveboss=extract_waveboss(Source(args.source))
    (ROOT/'reference/waveboss.json').write_text(json.dumps(waveboss,indent=2)+'\n')
    for i,seg in enumerate(waveboss['segments']):native_clip('waveboss_'+str(i),seg['clip']['frames'],seg['clip']['loop'])
    body.append('const WaveBossSegment waveboss_segments[]={'+','.join('{&waveboss_%d,{%d,%d},%d}'%(i,*seg['next'],seg['event']) for i,seg in enumerate(waveboss['segments']))+'};')
    body.append('const u16 waveboss_roots[]={'+','.join(map(str,waveboss['roots']))+'},waveboss_scores[]={'+','.join(map(str,waveboss['scores']))+'};')
    body.append('const LargeContactShape waveboss_shapes[]={'+','.join('{'+','.join(map(str,shape))+'}' for shape in waveboss['contact_shapes'])+'};')
    for name in ('health','layers'):body.append('const u8 waveboss_'+name+'[]={'+','.join(map(str,waveboss[name]))+'};')
    body.append('const u8 waveboss_choices[2][16]={'+','.join('{'+','.join(map(str,c))+'}' for c in waveboss['choices'])+'};')
    eruption=extract_eruption(Source(args.source))
    (ROOT/'reference/eruption.json').write_text(json.dumps(eruption,indent=2)+'\n')
    for i,seg in enumerate(eruption['segments']):native_clip('eruption_'+str(i),seg['clip']['frames'],seg['clip']['loop'])
    body.append('const AnimClip *const eruption_clips[]={'+','.join('&eruption_'+str(i) for i in range(len(eruption['segments'])))+'};')
    teleporter=extract_teleporter(Source(args.source))
    (ROOT/'reference/teleporter.json').write_text(json.dumps(teleporter,indent=2)+'\n')
    for i,seg in enumerate(teleporter['segments']):native_clip('teleporter_'+str(i),seg['clip']['frames'],seg['clip']['loop'])
    body.append('const AnimSegment teleporter_segments[]={'+','.join('{&teleporter_%d,%d,%d}'%(i,seg['next'],seg['event']) for i,seg in enumerate(teleporter['segments']))+'};')
    body.append('const u16 teleporter_roots[]={'+','.join(map(str,teleporter['roots']))+'},teleporter_score='+str(teleporter['score'])+';')
    body.append('const u8 teleporter_health[]={'+','.join(map(str,teleporter['health']))+'}' +',teleporter_positions[8][2]={'+','.join('{%d,%d}'%tuple(p) for p in teleporter['positions'])+'};')
    hunter=extract_hunter(Source(args.source))
    (ROOT/'reference/hunter.json').write_text(json.dumps(hunter,indent=2)+'\n')
    for i,seg in enumerate(hunter['segments']):native_clip('hunter_'+str(i),seg['clip']['frames'],seg['clip']['loop'])
    body.append('const HunterSegment hunter_segments[]={'+','.join('{&hunter_%d,%d,%d}'%(i,seg['next'],seg['event']) for i,seg in enumerate(hunter['segments']))+'};')
    body.append('const u16 hunter_roots[]={'+','.join(map(str,hunter['roots']))+'},hunter_score='+str(hunter['score'])+';')
    for name in ('choices','health','layers','reset_health'):body.append('const u8 hunter_'+name+'[]={'+','.join(map(str,hunter[name]))+'};')
    fighter=extract_reinforcement_body(Source(args.source))
    (ROOT/'reference/reinforcement_body.json').write_text(json.dumps(fighter,indent=2)+'\n')
    for i,seg in enumerate(fighter['segments']):native_clip('fighter_'+str(i),seg['clip']['frames'],seg['clip']['loop'])
    body.append('const AnimSegment reinforcement_segments[]={'+','.join('{&fighter_%d,%d,%d}'%(i,seg['next'],seg['event']) for i,seg in enumerate(fighter['segments']))+'};')
    body.append('const u16 reinforcement_roots[2][25]={'+','.join('{'+','.join(map(str,r))+'}' for r in fighter['roots'])+'};')
    body.append('const u8 reinforcement_choices[2][8][16]={'+','.join('{'+','.join('{'+','.join(map(str,r))+'}' for r in p)+'}' for p in fighter['choices'])+'};')
    body.append('const u8 reinforcement_health[2]={'+','.join(map(str,fighter['health']))+'},reinforcement_layers[2]={'+','.join(map(str,fighter['layers']))+'};const u16 reinforcement_scores[2]={'+','.join(map(str,fighter['scores']))+'};')
    for i,shot in enumerate(fighter['shots'][0]):
        other=fighter['shots'][1][i]
        assert [{k:v for k,v in f.items() if k!='source_address'} for f in shot['clip']['frames']]==[{k:v for k,v in f.items() if k!='source_address'} for f in other['clip']['frames']]
        native_clip('fighter_shot_'+str(i),shot['clip']['frames'],None)
    body.append('const AnimClip *const reinforcement_clips[12]={'+','.join('&fighter_shot_'+str(i) for i in range(12))+'};')
    crawler=extract_crawler(Source(args.source))
    (ROOT/'reference/crawler.json').write_text(json.dumps(crawler,indent=2)+'\n')
    for i,seg in enumerate(crawler['segments']):native_clip('crawler_'+str(i),seg['clip']['frames'],seg['clip']['loop'])
    body.append('const CrawlerSegment crawler_segments[]={'+','.join('{&crawler_%d,%d,%d}'%(i,seg['next'],seg['event']) for i,seg in enumerate(crawler['segments']))+'};')
    body.append('const u16 crawler_roots[]={'+','.join(map(str,crawler['roots']))+'};')
    body.append('const u16 crawler_scores[]={'+','.join(map(str,crawler['scores']))+'};')
    body.append('const u8 crawler_health[]={'+','.join(map(str,crawler['health']))+'};')
    statue=extract_statue(Source(args.source))
    (ROOT/'reference/statue.json').write_text(json.dumps(statue,indent=2)+'\n')
    for i,seg in enumerate(statue['segments']):native_clip('statue_'+str(i),seg['clip']['frames'],seg['clip']['loop'])
    body.append('const StatueSegment statue_segments[]={'+','.join('{&statue_%d,%d,%d}'%(i,seg['next'],seg['event']) for i,seg in enumerate(statue['segments']))+'};')
    body.append('const u16 statue_roots[]={'+','.join(map(str,statue['roots']))+'},statue_score='+str(statue['score'])+';')
    body.append('const u8 statue_choices[]={'+','.join(map(str,statue['choices']))+'},statue_health='+str(statue['health'])+',statue_layers='+str(statue['layers'])+',statue_reset_health='+str(statue['reset_health'])+';')
    checkpoint=extract_checkpoint(Source(args.source))
    (ROOT/'reference/checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n')
    body.append('const u16 checkpoint_grid[8][32][2]='+str(checkpoint['grids']).replace('[','{').replace(']','}')+';')
    body.append('const u8 checkpoint_wide[8]={'+','.join(map(str,checkpoint['wide']))+'};')
    body.append('const u16 checkpoint_player_x='+str(checkpoint['player_offset'][0])+',checkpoint_player_y='+str(checkpoint['player_offset'][1])+';')
    progress=extract_progress(Source(args.source))
    progress['initial_lives']=json.loads((ROOT/'reference/progress_oracle.json').read_text())['initial'][0]
    (ROOT/'reference/progress.json').write_text(json.dumps(progress,indent=2)+'\n')
    body.append('const u32 progress_thresholds[4]={'+','.join(map(str,progress['thresholds']))+'};')
    body.append('const u16 progress_initial_coins='+str(progress['initial_coins'])+';')
    body.append('const u8 progress_initial_health='+str(progress['initial_health'])+',progress_initial_armor='+str(progress['initial_armor'])+',progress_initial_lives='+str(progress['initial_lives'])+';')
    shop=extract_shop(Source(args.source))
    shop['default_difficulty']=json.loads((ROOT/'reference/shop_oracle.json').read_text())['default_difficulty']
    (ROOT/'reference/shop.json').write_text(json.dumps(shop,indent=2)+'\n')
    body.append('const u16 shop_prices[2][8][4]='+str(shop['prices']).replace('[','{').replace(']','}')+';')
    body.append('const u16 shop_key_price='+str(shop['key_price'])+',shop_antidote_price='+str(shop['antidote_price'])+';')
    body.append('const u8 shop_grid[12]={'+','.join(map(str,shop['grid']))+'},shop_default_difficulty='+str(shop['default_difficulty'])+';')
    containers=extract_container(Source(args.source))
    (ROOT/'reference/container.json').write_text(json.dumps(containers,indent=2)+'\n')
    body.append('const u8 container_initial[8][8]={'+','.join('{'+','.join(map(str,row))+'}' for row in containers['round_contents'])+'};')
    body.append('const u16 container_coin_values[4]={'+','.join(map(str,containers['coin_values']))+'};')
    for i,seg in enumerate(containers['segments']):native_clip('container_'+str(i),seg['clip']['frames'],seg['clip']['loop'])
    body.append('const ContainerSegment container_segments[]={'+','.join('{&container_%d,%d,%d}'%(i,seg['next'],seg['event']) for i,seg in enumerate(containers['segments']))+'};')
    body.append('const u16 container_wave_roots[]={'+','.join(map(str,containers['wave_roots']))+'};')
    body.append('const u16 container_roots[]={'+','.join(map(str,containers['roots']))+'};')
    body.append('const u16 container_trap_roots[]={'+','.join(map(str,containers['trap_roots']))+'};')
    pair=extract_pair(Source(args.source))
    (ROOT/'reference/pair.json').write_text(json.dumps(pair,indent=2)+'\n')
    for i,seg in enumerate(pair['segments']):native_clip('pair_'+str(i),seg['clip']['frames'],seg['clip']['loop'])
    body.append('const PairSegment pair_segments[]={'+','.join('{&pair_%d,%d,%d}'%(i,seg['next'],seg['event']) for i,seg in enumerate(pair['segments']))+'};')
    body.append('const u16 pair_roots[]={'+','.join(map(str,pair['roots']))+'};')
    body.append('const u8 pair_choices[]={'+','.join(map(str,pair['choices']))+'};')
    body.append('const u16 pair_score=%d;'%pair['score'])
    boulder=extract_boulder(Source(args.source))
    body.append('const u16 boulder_weapon_score=%d;'%boulder['weapon_score'])
    (ROOT/'reference/boulder.json').write_text(json.dumps(boulder,indent=2)+'\n')
    for i,seg in enumerate(boulder['segments']):native_clip('boulder_'+str(i),seg['clip']['frames'],None)
    body.append('const BoulderSegment boulder_segments[]={'+','.join('{&boulder_%d,{%d,%d},%d}'%(i,*seg['next'],seg['event']) for i,seg in enumerate(boulder['segments']))+'};')
    body.append('const u16 boulder_roots[]={'+','.join(map(str,boulder['roots']))+'};')
    body.append('const u8 boulder_initial_damage=%d,boulder_bounce_damage=%d;'%(boulder['damage'],boulder['bounce_damage']))
    for prefix,upper in [('boss',False),('boss_upper',True)]:
        boss_motion=extract_boss_motion(Source(args.source),upper)
        (ROOT/('reference/'+prefix+'_motion.json')).write_text(json.dumps(boss_motion,indent=2)+'\n')
        for i,seg in enumerate(boss_motion['segments']):native_clip(prefix+'_'+str(i),seg['clip']['frames'],None)
        body.append('const BossSegment '+prefix+'_segments[]={'+','.join('{&%s_%d,{%d,%d},%d}'%(prefix,i,*seg['next'],seg['event']) for i,seg in enumerate(boss_motion['segments']))+'};')
        body.append('const u16 '+prefix+'_roots[]={'+','.join(map(str,boss_motion['roots']))+'};')
        body.append('const u8 '+prefix+'_choices[]={'+','.join(map(str,boss_motion['choices']))+'};')
    bosses=extract_boss(Source(args.source))
    (ROOT/'reference/boss_layers.json').write_text(json.dumps(bosses,indent=2)+'\n')
    body.append('const u8 layered_boss_layers[]={'+','.join(map(str,bosses['layers']))+'};')
    body.append('const u8 layered_boss_reset_health=%d;const u16 layered_boss_score=%d;'%(bosses['reset_health'],bosses['score']))
    for key in ('component_counts','upper_health'):
        body.append('const u8 boss_'+key+'[]={'+','.join(map(str,bosses[key]))+'};')
    for key in ('upper_layers','upper_damage','upper_reset_health','upper_score'):
        body.append('const u8 boss_'+key+'='+str(bosses[key])+';')
    combat_source=Source(args.source)
    combat_source.expect(7,0x8b05,'2116913aacf3875f1600197e321cf4237e320df4')
    combat_source.expect(7,0xa0fd,'2190a2016000edb0')
    knives=combat_source.read(7,0xa290,96)
    assert all(knives[i+16:i+18]==knives[16:18] for i in (0,32,64))
    body.append('const u8 dagger_width=%d,dagger_height=%d;'%(knives[16],knives[17]))
    weapon_table=combat_source.read(7,0x9116,10)
    body.append('const u8 player_weapon_damage[]={'+','.join(map(str,weapon_table[1::2]))+'};')
    (ROOT/'reference/player_weapon.json').write_text(json.dumps({'damage':list(weapon_table[1::2]),'source_set':combat_source.lock['aggregate_sha256'],'witnesses':list(combat_source.witnesses.values())},indent=2)+'\n')
    zombie=extract_zombie(Source(args.source))
    (ROOT/'reference/zombie.json').write_text(json.dumps(zombie,indent=2)+'\n')
    for i,seg in enumerate(zombie['segments']):native_clip('zombie_'+str(i),seg['clip']['frames'],None)
    body.append('const SkeletonSegment zombie_segments[]={'+','.join('{&zombie_%d,%d,%d}'%(i,seg['next'],seg['event']) for i,seg in enumerate(zombie['segments']))+'};')
    body.append('const u16 zombie_roots[]={'+','.join(map(str,zombie['roots']))+'};')
    body.append('const u8 zombie_spawn_x[]={'+','.join(map(str,zombie['spawn_x']))+'};')
    body.append('const u8 zombie_lifetime=%d;const u16 zombie_score=%d;'%(zombie['lifetime'],zombie['score']))
    thrower=extract_thrower(Source(args.source))
    (ROOT/'reference/thrower.json').write_text(json.dumps(thrower,indent=2)+'\n')
    throw_events=['disable_contact','enable_contact','choose_walk_or_throw','walk_step','fall_step','death_drop','retire','throw','jump_start','jump_step','projectile_hit']
    for i,seg in enumerate(thrower['segments']):native_clip('thrower_'+str(i),seg['clip']['frames'],None)
    body.append('const SkeletonSegment thrower_segments[]={'+','.join('{&thrower_%d,%d,%d}'%(i,seg['next'] if seg['next'] is not None else 65535,throw_events.index(seg['event'])) for i,seg in enumerate(thrower['segments']))+'};')
    body.append('const u16 thrower_roots[]={'+','.join(map(str,thrower['roots']))+'};')
    body.append('const u8 thrower_spawn_x[]={'+','.join(map(str,thrower['spawn_x']))+'};')
    body.append('const u8 thrower_health=%d,thrower_lifetime=%d;const u16 thrower_score=%d;'%(thrower['actor']['health'],thrower['actor']['cycles'],thrower['score']))
    body.append('const u8 thrower_shot_damage=%d,thrower_shot_width=%d,thrower_shot_height=%d,thrower_shot_health=%d;'%(thrower['projectile']['damage'],thrower['projectile']['width'],thrower['projectile']['height'],thrower['projectile']['health']))
    spitter=extract_spitter(Source(args.source))
    (ROOT/'reference/spitter.json').write_text(json.dumps(spitter,indent=2)+'\n')
    throw_events=['disable_contact','enable_contact','choose_walk_or_throw','walk_step','fall_step','death_drop','retire','throw','jump_start','jump_step','projectile_hit']
    for i,seg in enumerate(spitter['segments']):native_clip('spitter_'+str(i),seg['clip']['frames'],None)
    body.append('const SkeletonSegment spitter_segments[]={'+','.join('{&spitter_%d,%d,%d}'%(i,seg['next'] if seg['next'] is not None else 65535,throw_events.index(seg['event'])) for i,seg in enumerate(spitter['segments']))+'};')
    body.append('const u16 spitter_roots[]={'+','.join(map(str,spitter['roots']))+'};')
    body.append('const u8 spitter_spawn_x[]={'+','.join(map(str,spitter['spawn_x']))+'};')
    body.append('const u8 spitter_health=%d,spitter_lifetime=%d;const u16 spitter_score=%d;'%(spitter['actor']['health'],spitter['actor']['cycles'],spitter['score']))
    body.append('const u8 spitter_shot_damage=%d,spitter_shot_width=%d,spitter_shot_height=%d,spitter_shot_health=%d;'%(spitter['projectile']['damage'],spitter['projectile']['width'],spitter['projectile']['height'],spitter['projectile']['health']))
    wisp=extract_wisp(Source(args.source))
    (ROOT/'reference/wisp.json').write_text(json.dumps(wisp,indent=2)+'\n')
    for i,seg in enumerate(wisp['segments']):native_clip('wisp_'+str(i),seg['clip']['frames'],None)
    body.append('const WispSegment wisp_segments[]={'+','.join('{&wisp_%d,{%d,%d},%d}'%(i,*seg['next'],seg['event']) for i,seg in enumerate(wisp['segments']))+'};')
    body.append('const u16 wisp_roots[]={'+','.join(map(str,wisp['roots']))+'};')
    emerging=extract_emerge(Source(args.source))
    (ROOT/'reference/emerge.json').write_text(json.dumps(emerging,indent=2)+'\n')
    for i,p in enumerate(emerging['profiles']):
        for j,c in enumerate(p['clips']):native_clip('emerge_%d_%d'%(i,j),c['frames'],None)
    body.append('const EmergeProfile emerge_profiles[]={'+','.join('{{'+','.join('&emerge_%d_%d'%(i,j) for j in range(6))+'},%d,%d,%d,%d}'%(p['score'],p['health'],p['width'],p['height']) for i,p in enumerate(emerging['profiles']))+'};')
    pickup=extract_pickup(Source(args.source))
    (ROOT/'reference/pickup.json').write_text(json.dumps(pickup,indent=2)+'\n')
    assert all(v['half_width']==8 and v['half_height']==8 for v in pickup['variants'])
    body.append('const u8 pickup_width=8,pickup_height=8,pickup_seconds=%d;'%pickup['time_seconds'])
    hazard=extract_hazard(Source(args.source))
    (ROOT/'reference/hazard.json').write_text(json.dumps(hazard,indent=2)+'\n')
    body.append('const u8 hazard_width=%d,hazard_height=%d,contact_player_width=%d,contact_player_height=%d;'%(hazard['half_width'],hazard['half_height'],hazard['player_half_width'],hazard['player_half_height']))
    sentry=extract_sentry(Source(args.source))
    (ROOT/'reference/sentry.json').write_text(json.dumps(sentry,indent=2)+'\n')
    for i,c in enumerate(sentry['clips']):native_clip('sentry_'+str(i),c['frames'],None)
    body.append('const AnimClip *const sentry_clips[]={'+','.join('&sentry_'+str(i) for i in range(7))+'};')
    body.append('const u8 aim_table[]={'+','.join(map(str,sentry['aim_table']))+'};')
    body.append('const u8 sentry_health=%d; const u16 sentry_score=%d;'%(sentry['health'],sentry['score']))
    loot_data=extract_loot(Source(args.source))
    (ROOT/'reference/loot.json').write_text(json.dumps(loot_data,indent=2)+'\n')
    for k in loot_data['kinds']:native_clip('loot_'+str(k['kind']),k['clip']['frames'],None)
    body.append('const AnimClip *const loot_clips[]={'+','.join('&loot_'+str(i) for i in range(1,8))+'};')
    body.append('const u16 loot_values[]={'+','.join(str(k['coins']) for k in loot_data['kinds'])+'};')
    body.append('const u8 drop_table[28][32]={'+','.join('{'+','.join(map(str,row))+'}' for row in loot_data['tables'])+'};')
    # Constructors identified by bank/address. Keep identity only in conversion report.
    # Families: walker, flyer, turret, falling rock, hazard, chest, captive, pickup, boss.
    family={(0,0x93ed):0,(0,0x8000):0,(0,0x8389):0,(0,0x89c6):0,(0,0x9b85):1,(0,0xa35c):0,
      (0,0xab33):0,(0,0xab4a):0,(0,0xb84f):2,(1,0xb2a9):4,(1,0xacbe):5,(1,0xacd3):5,
      (2,0xacac):1,(2,0xb67f):2,(2,0x8000):0,(2,0x8344):0,(3,0xaab3):0,(4,0xb338):1,
      (4,0xb4af):7,(4,0xb515):7,(2,0xa6f8):2,(1,0x8a03):1,(1,0x8a5d):1,(1,0x8d33):1}
    actor_contract=load_actor_contract(Source(args.source))
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
                    # No adjacent-code template scan or guessed 5/8-byte animation stride.
                    kind=family.get(key,0);code=0x280;attr=0x45;frames=1;hp=3
                    observed=actor_contract[key]
                    npc_kind=0
                    if 0x5e32<=pc<=0x5eb0 and (pc-0x5e32)%18==0:
                        npc_kind=1+(pc-0x5e32)//18;kind=6;code=0x300;attr=0x64;hp=0
                    if key in ((2,0x8ef4),(3,0x8000),(3,0x991d),(3,0x9b24),(3,0xb7f3),(0,0xb1c1),(4,0x9eb1),(4,0x9f16)):kind=8;hp=48+r*8
                    if key==(0,0x93ed):code=0x280;attr=0x45;frames=3
                    if key==(0,0x8000):code=0x240;attr=0x42;frames=3
                    if key==(2,0x8000):code=0x3c0;attr=0x63;frames=3
                    if key[0]==2 and 0xb7da<=pc<=0xb8d7 and (pc-0xb7da)%23==0:kind=9
                    size=1 if kind in (4,7) else 4
                    if observed['health'] is not None:hp=observed['health']
                    if observed['initial_frame'] is not None:
                        first=observed['initial_frame'];code=first['code'];attr=first['palette'];size=first['pieces'];frames=1
                    defs[key]={'id':len(defs),'bank':key[0],'address':pc,'kind':kind,'code':code,'palette':attr&7,'hp':hp,'pieces':size,'frames':frames,'npc_kind':npc_kind,'behavior_verified':False,'constructor_evidence':observed}

                rows[(x,y,k)]=(x,y,defs[key]['id'],k)
        spawns.append(sorted(rows.values()))
    ds=[]
    for d in defs.values():ds.append('{'+','.join(map(str,[d['code'],d['kind'],d['palette'],d['hp'],d['pieces'],d['frames'],d['npc_kind']]))+'}')
    body.append('const ActorDef actor_defs[]={'+','.join(ds)+'};');report['actor_definitions']=list(defs.values())
    body.append('const u8 container_left[]={'+','.join('1' if d['bank']==1 and d['address']==0xacd3 else '0' for d in defs.values())+'};')
    body.append('const u8 flailer_kinds[]={'+','.join(str({0xab33:1,0xab4a:2,0xb1c1:3,0xb1d8:4}.get(d['address'],0)) if d['bank']==0 else '0' for d in defs.values())+'};')
    body.append('const u8 waveboss_kinds[]={'+','.join(str({0x98a3:1,0x98e8:2}.get(d['address'],0)) if d['bank']==1 else '0' for d in defs.values())+'};')
    body.append('const u8 eruption_kinds[]={'+','.join(str({0x8a5d:1,0x8a03:2,0x8b9b:3,0x8bf5:4}.get(d['address'],0)) if d['bank']==1 else '0' for d in defs.values())+'};')
    body.append('const u8 teleporter_kinds[]={'+','.join(str({0x92e6:1,0x8d33:2}.get(d['address'],0)) if d['bank']==1 else '0' for d in defs.values())+'};')
    body.append('const u8 hunter_kinds[]={'+','.join(str(1+(d['address']==0x9fc4)) if d['bank']==1 and d['address'] in (0x9f83,0x9fc4) else '0' for d in defs.values())+'};')
    body.append('const u8 edge_spawn_kinds[]={'+','.join('1' if (d['bank'],d['address'])==(4,0xa4d0) else '0' for d in defs.values())+'};')
    body.append('const u8 reinforcement_kinds[]={'+','.join(str({(2,0x8344):1,(2,0x9af6):2}.get((d['bank'],d['address']),0)) for d in defs.values())+'};')
    body.append('const u8 crawler_kinds[]={'+','.join(str({(3,0xaab3):1,(3,0xb153):2,(7,0xa3b6):3}.get((d['bank'],d['address']),0)) for d in defs.values())+'};')
    body.append('const u8 statue_kinds[]={'+','.join('1' if d['bank']==0 and d['address']==0xb84f else '0' for d in defs.values())+'};')
    body.append('const u8 pair_kinds[]={'+','.join('1' if d['bank']==2 and d['address']==0xacac else '0' for d in defs.values())+'};')
    body.append('const u8 boulder_kinds[]={'+','.join('1' if d['bank']==4 and d['address']==0xb338 else '0' for d in defs.values())+'};')
    body.append('const u8 stone_kinds[]={'+','.join('1' if d['bank']==4 and d['address']==0x9a4c else '0' for d in defs.values())+'};')
    body.append('const u8 layered_boss_kinds[]={'+','.join(str((0x9eb1,0x9f16).index(d['address'])+1) if d['bank']==4 and d['address'] in (0x9eb1,0x9f16) else '0' for d in defs.values())+'};')
    body.append('const u8 zombie_kinds[]={'+','.join(str((0x8000,0x8389,0x89c6).index(d['address'])+1) if d['bank']==0 and d['address'] in (0x8000,0x8389,0x89c6) else '0' for d in defs.values())+'};')
    body.append('const u8 wisp_kinds[]={'+','.join('1' if d['bank']==2 and d['address']==0xa6f8 else '0' for d in defs.values())+'};')
    body.append('const u8 emerge_kinds[]={'+','.join(str((0x8000,0x81a2).index(d['address'])+1) if d['bank']==2 and d['address'] in (0x8000,0x81a2) else '0' for d in defs.values())+'};')
    body.append('const u8 pickup_kinds[]={'+','.join(str((0xb4af,0xb515).index(d['address'])+1) if d['bank']==4 and d['address'] in (0xb4af,0xb515) else '0' for d in defs.values())+'};')
    body.append('const u8 actor_damage[]={'+','.join(str(d['constructor_evidence']['damage'] if d['constructor_evidence']['damage'] is not None else 1) for d in defs.values())+'};')
    for field in ('pool','half_width','half_height'):
        body.append('const u8 actor_contact_'+field+'[]={'+','.join(str((d['constructor_evidence']['contact'] or {}).get(field,0)) for d in defs.values())+'};')
    body.append('const u8 screen_attack_targets[]={'+','.join('1' if d['constructor_evidence']['screen_attack_target'] else '0' for d in defs.values())+'};')
    body.append('const u8 hazard_kinds[]={'+','.join('1' if d['bank']==1 and d['address']==0xb2a9 else '0' for d in defs.values())+'};')
    body.append('const u8 sentry_kinds[]={'+','.join('1' if d['bank']==2 and d['address']==0xb67f else '0' for d in defs.values())+'};')
    body.append('const u8 drop_categories[]={'+','.join(str(d['constructor_evidence']['category']) if d['constructor_evidence']['category'] is not None and d['constructor_evidence']['category']<28 else '255' for d in defs.values())+'};')
    body.append('const u8 skeleton_kinds[]={'+','.join(str(skeleton['constructors'].index(d['address'])) if d['bank']==0 and d['address'] in skeleton['constructors'] else '255' for d in defs.values())+'};')
    body.append('const u8 hidden_kinds[]={'+','.join(str((d['address']-0xb7da)//23) if d['kind']==9 else '255' for d in defs.values())+'};')
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
        # Hidden terrain uses the source's tile 0 / palette 6 replacement.
        opened=np.array(pm[6],dtype=np.uint8)[tiles[0]];open_words=[]
        for oy,ox in ((0,0),(0,8),(8,0),(8,8)):
            cell=opened[oy:oy+8,ox:ox+8]
            b,flags=min((pack(cell),0),(pack(cell[:,::-1]),0x800),(pack(cell[::-1,:]),0x1000),(pack(cell[::-1,::-1]),0x1800))
            if b not in unique:unique[b]=len(unique);pats.extend(b)
            open_words.append((unique[b]+16)|(int(groups[6])<<13)|flags)
        body.append(f'const u16 open_tile{r}[]={{'+','.join(map(str,open_words))+'};')
        patch_rows=[]
        for patch in hidden['rounds'][r]:
            matches=[i for i,row in enumerate(spawns[r]) if row[3]==patch['persistent'] and list(defs.values())[row[2]]['kind']==9]
            assert len(matches)==1,(r,patch,matches)
            i=matches[0];assert spawns[r][i][:2]==(patch['x'],patch['y']+8)
            patch_rows.append('{%d,%d}'%(patch['cell'],i))
        body.append(f'const WorldPatch patches{r}[]={{'+','.join(patch_rows)+'};')
        # Row-major 8x8 map enables contiguous strip uploads; only the entering edges stream.
        wm=[]
        for y in range(h*2):
            for x in range(w*2):wm.append(world[(y//2)*w+x//2][(y&1)*2+(x&1)])
        assert len(unique)<1700,(r,len(unique))
        emit(f'bg{r}',bytes(pats),'u32');emit(f'map{r}',words(wm));emit(f'pal{r}',words(palettes));emit(f'collision{r}',bytes(coll),'u8')
        spawn=spawns[r];body.append(f'const Spawn spawn{r}[]={{'+','.join('{'+','.join(map(str,s))+'}' for s in spawn)+'};')
        preview.resize((w*8,h*8)).save(ROOT/f'reports/round{r+1}.png')
        report['rounds'].append({'round':r+1,'width':w*16,'height':h*16,'camera':[cx,cy],'layout':layout,'patterns':len(unique),'spawns':len(spawn),'collision_codes':dict(Counter(coll))})
    body.append('const Round rounds[8]={'+',\n'.join('{bg%d,map%d,pal%d,collision%d,spawn%d,%d,%d,%d,%d,%d,%d,patches%d,open_tile%d,%d,%d}'%(r,r,r,r,r,d['patterns'],d['spawns'],d['width'],d['height'],*d['camera'],r,r,len(hidden['rounds'][r]),collision[0]) for r,d in enumerate(report['rounds']))+'};')
    (ROOT/'res/assets.res').write_text('\n'.join(resources)+'\n')
    (ROOT/'inc/assets.h').write_text('#ifndef ASSETS_H\n#define ASSETS_H\n#include "game.h"\n#include "animation.h"\n#include "boss.h"\n#include "boulder.h"\n#include "pair.h"\n#include "container.h"\nextern const ContainerSegment container_segments[];\nextern const u16 container_roots[],container_trap_roots[],container_wave_roots[];\n#include "flailer.h"\nextern const AnimSegment flailer_segments[];\nextern const u16 flailer_roots[2][21],flailer_scores[];\nextern const u8 flailer_kinds[],flailer_health[];\n#include "large_contact.h"\nextern const LargeContactShape waveboss_shapes[];\n#include "waveboss.h"\nextern const WaveBossSegment waveboss_segments[];\nextern const u16 waveboss_roots[],waveboss_scores[];\nextern const u8 waveboss_kinds[],waveboss_health[],waveboss_layers[],waveboss_choices[2][16];\n#include "eruption.h"\nextern const AnimClip *const eruption_clips[];\nextern const u8 eruption_kinds[];\n#include "teleporter.h"\nextern const AnimSegment teleporter_segments[];\nextern const u16 teleporter_roots[],teleporter_score;\nextern const u8 teleporter_kinds[],teleporter_health[],teleporter_positions[8][2];\n#include "hunter.h"\nextern const HunterSegment hunter_segments[];\nextern const u16 hunter_roots[],hunter_score;\nextern const u8 hunter_kinds[],hunter_choices[],hunter_health[],hunter_layers[],hunter_reset_health[];\n#include "reinforcement_body.h"\n#include "crawler.h"\nextern const CrawlerSegment crawler_segments[];\nextern const u16 crawler_roots[],crawler_scores[];\nextern const u8 edge_spawn_kinds[],reinforcement_kinds[];\nextern const u8 crawler_kinds[],crawler_health[];\n#include "statue.h"\nextern const StatueSegment statue_segments[];\nextern const u16 statue_roots[],statue_score;\nextern const u8 statue_kinds[],statue_choices[],statue_health,statue_layers,statue_reset_health;\nextern const u16 checkpoint_grid[8][32][2],checkpoint_player_x,checkpoint_player_y;\nextern const u8 checkpoint_wide[8];\nextern const u32 progress_thresholds[4];\nextern const u16 progress_initial_coins;\nextern const u8 progress_initial_health,progress_initial_armor,progress_initial_lives;\nextern const u16 shop_prices[2][8][4],shop_key_price,shop_antidote_price;\nextern const u8 shop_grid[12],shop_default_difficulty;\nextern const u8 container_left[],container_initial[8][8];\nextern const u16 container_coin_values[4];\nextern const PairSegment pair_segments[];\nextern const u16 pair_roots[],pair_score;\nextern const u8 pair_kinds[],pair_choices[];\nextern const BoulderSegment boulder_segments[];\nextern const u16 boulder_roots[],boulder_weapon_score;\nextern const u8 boulder_kinds[],boulder_initial_damage,boulder_bounce_damage;\nextern const u8 boss_component_counts[],boss_upper_health[],boss_upper_layers,boss_upper_damage,boss_upper_reset_health,boss_upper_score;\nextern const BossSegment boss_segments[],boss_upper_segments[];\nextern const u16 boss_roots[],boss_upper_roots[];\nextern const u8 boss_choices[],boss_upper_choices[];\n#include "skeleton.h"\n#include "emerge.h"\n#include "wisp.h"\nextern const SkeletonSegment spitter_segments[];\nextern const u16 spitter_roots[],spitter_score;\nextern const u8 spitter_spawn_x[],spitter_health,spitter_lifetime,spitter_shot_damage,spitter_shot_width,spitter_shot_height,spitter_shot_health;\nextern const SkeletonSegment thrower_segments[];\nextern const u16 thrower_roots[],thrower_score;\nextern const u8 thrower_spawn_x[],thrower_health,thrower_lifetime,thrower_shot_damage,thrower_shot_width,thrower_shot_height,thrower_shot_health;\nextern const SkeletonSegment zombie_segments[];\nextern const u16 zombie_roots[],zombie_score;\nextern const u8 zombie_kinds[],zombie_lifetime,zombie_spawn_x[];\nextern const WispSegment wisp_segments[];\nextern const u16 wisp_roots[7];\nextern const u8 wisp_kinds[];\nextern const EmergeProfile emerge_profiles[2];\nextern const u8 emerge_kinds[];\nextern const AnimClip npc_idle, npc_released, npc_rescue;\nextern const AnimClip *const hidden_clips[12];\nextern const AnimClip hidden_life_collected, hidden_explosion;\nextern const u8 hidden_kinds[];\nextern const u8 skeleton_kinds[];\nextern const AnimClip *const sentry_clips[7];\nextern const u8 pickup_kinds[],screen_attack_targets[],pickup_width,pickup_height,pickup_seconds;\nextern const u8 stone_kinds[],layered_boss_kinds[],layered_boss_layers[],layered_boss_reset_health;\nextern const u16 layered_boss_score;\nextern const u8 actor_damage[],player_weapon_damage[5],dagger_width,dagger_height;\nextern const u8 actor_contact_pool[],actor_contact_half_width[],actor_contact_half_height[];\nextern const u8 hazard_kinds[],hazard_width,hazard_height,contact_player_width,contact_player_height;\nextern const u8 sentry_kinds[], aim_table[64], sentry_health;\nextern const u16 sentry_score;\nextern const AnimClip *const loot_clips[7];\nextern const u16 loot_values[7];\nextern const u8 drop_table[28][32], drop_categories[];\nextern const SkeletonSegment skeleton_segments[];\nextern const SkeletonProfile skeleton_profiles[3];\n'+'\n'.join(decl)+'\nextern const HeroFrame hero_frames[10][16];\nextern const ActorDef actor_defs[];\nextern const Round rounds[8];\n#endif\n')
    (ROOT/'src/data.c').write_text('/* Generated by tools/extract.py. */\n#include <genesis.h>\n#include "assets.h"\n'+'\n'.join(body)+'\n')
    report['outputs']={p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in OUT.glob('*.bin')}
    (ROOT/'reports/assets.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['rounds'],indent=2));print('native asset bytes',sum(p.stat().st_size for p in OUT.glob('*.bin')))
if __name__=='__main__':main()
