"""Convert observed FM music into timed YM2612 data, never executable ROM code."""
from pathlib import Path
import json,hashlib
from arcade_source import Source
ROOT=Path(__file__).resolve().parents[1]
COMMANDS=tuple(c for c in range(0x20,0x3a) if c!=0x38)
def convert(command):
 folder=ROOT/'reference/music';raw=(folder/f'{command:02x}.txt').read_bytes();meta=json.loads((folder/f'{command:02x}.json').read_text())
 assert hashlib.sha256(raw).hexdigest()==meta['trace_sha256']
 assert hashlib.sha256((ROOT/'tools/music_oracle.lua').read_bytes()).hexdigest()==meta['lua_sha256']
 lines=raw.decode().splitlines();head=lines[0].split('|');kind=head[0];assert kind in ('LOOP','END')
 start,end=(int(head[1]),int(head[2])) if kind=='LOOP' else (65535,int(head[1]))
 high=[0,0];cache={};groups={};frequencies={};algorithms={};levels={}
 carriers=(8,8,8,8,12,14,14,15)
 def emit(t,p,r,v,force=False):
  if force or cache.get((p,r))!=v:groups.setdefault(t,[]).append((p,r,v));cache[p,r]=v
 for line in lines[1:-1]:
  _,t,p,r,v=line.split('|');t,p,r,v=map(int,(t,p,r,v))
  if 0xa4<=r<=0xa6:high[p]=v;continue
  if 0xa0<=r<=0xa2:
   original=((high[p]&7)<<8)|v
   f=(original*14+7)//15;value=((high[p]&0x38)<<8)|f
   if frequencies.get((p,r))==value:continue
   frequencies[p,r]=value
   emit(t,p,r+4,(high[p]&0x38)|(f>>8),True);emit(t,p,r,f&255,True)
  elif r==0x28:emit(t,0,r,(v&0xf3)|(p<<2),True)
  elif 0x40<=r<=0x4e:
   ch=r&3;slot=(r>>2)&3;levels[p,r]=v
   emit(t,p,r,min(127,v+(12 if carriers[algorithms.get((p,ch),0)]&(1<<slot) else 0)))
  elif 0xb0<=r<=0xb2:
   ch=r-0xb0;algorithms[p,ch]=v&7;emit(t,p,r,v)
   for slot in range(4):
    reg=0x40+4*slot+ch;level=levels.get((p,reg),127)
    emit(t,p,reg,min(127,level+(12 if carriers[v&7]&(1<<slot) else 0)))
  else:
   assert 0x30<=r<=0x9f or 0xb0<=r<=0xb2,(p,r,v)
   emit(t,p,r,v)
 data=bytearray();loop_offset=None
 for t,events in sorted(groups.items()):
  if loop_offset is None and t>=start:loop_offset=len(data)
  assert len(events)<256
  data+=t.to_bytes(2,'big')+bytes([len(events)])+b''.join(bytes(e) for e in events)
 if kind=='END':loop_offset=0
 else:assert loop_offset is not None
 return data,dict(command=command,looping=kind=='LOOP',loop_tick=start,end_tick=end,loop_offset=loop_offset,bytes=len(data),writes=sum(map(len,groups.values())),source_writes=meta['writes'],trace_sha256=meta['trace_sha256'])
def generate():
 s=Source();s.expect(None,0x5a30,'29292a29292a292b')
 rows=['/* Generated native timed FM register data; no arcade program bytes. */','const u8 music_boss_commands[]={41,41,42,41,41,42,41,43};'];tracks=[]
 for command in COMMANDS:
  data,meta=convert(command);tracks.append(meta)
  rows.append('static const u8 music_%02x[]={%s};'%(command,','.join(map(str,data))))
 rows.append('static const MusicTrack music_tracks[26]={'+','.join('[%d]={music_%02x,%d,%d,%d,%d}'%(m['command']-0x20,m['command'],m['bytes'],m['loop_offset'],m['loop_tick'],m['end_tick']) for m in tracks)+'};')
 (ROOT/'src/music_data.inc').write_text('\n'.join(rows)+'\n')
 report=dict(tracks=tracks,bytes=sum(t['bytes'] for t in tracks),carrier_attenuation_steps=12,pitch_ratio='14/15 NTSC FM clock correction',timer_clock=3579545,timer_divisor=14328)
 (ROOT/'reference/music_conversion.json').write_text(json.dumps(report,indent=2)+'\n');print(report['bytes'])
if __name__=='__main__':generate()
