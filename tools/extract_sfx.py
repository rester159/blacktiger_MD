"""Compile finite SSG effects to native timed register data; no sound CPU code."""
import hashlib,json,math
from arcade_source import Source,ROOT

def generate():
 s=Source();ref=json.loads((ROOT/'reference/sfx_oracle.json').read_text())
 assert ref['source_set']==s.lock['aggregate_sha256']
 for k,p in [('trace_sha256','reference/sfx_oracle_events.txt'),('lua_sha256','tools/sfx_oracle.lua')]:assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==ref[k]
 cases=[]
 for l in (ROOT/'reference/sfx_oracle_events.txt').read_text().splitlines():
  f=l.split('|')
  if f[0]=='CASE':current=dict(command=int(f[1]),phase=int(f[2]),writes=[]);cases.append(current)
  elif f[0] in ('END','LOOP','BOUNDED'):current.update(kind=f[0],end=int(f[-1]))
  elif f[0]=='WRITE':current['writes'].append(tuple(map(int,f[1:])))
 data=s.files['bd-06.1l'];rows=[];tracks={};unique={};sizes=[];unsupported=set()
 for c in cases:
  if c['kind']!='END':unsupported.add(c['command']);continue
  cmd=c['command'];ptr=int.from_bytes(data[0xdc1+cmd*2:0xdc3+cmd*2],'little');flags=data[ptr];assert flags&128
  chip=(flags>>6)&1;groups={};cache={}
  for tick,part,reg,value in c['writes']:
   assert part==chip and reg<=10
   if reg in (8,9,10):assert value<16
   if cache.get(reg)!=value:groups.setdefault(tick,[]).append((reg,value));cache[reg]=value
  raw=bytearray()
  for tick,events in sorted(groups.items()):raw+=tick.to_bytes(2,'big')+bytes([len(events)])+bytes(v for pair in events for v in pair)
  raw=bytes(raw)
  if raw not in unique:
   name='sfx_data_'+str(len(unique));unique[raw]=name;rows.append('static const u8 '+name+'[]={'+','.join(map(str,raw))+'};');sizes.append(len(raw))
  tracks[cmd,c['phase']]=(unique[raw],len(raw),c['end'],flags)
 rows.append('static const SfxTrack sfx_tracks[64][4]={'+','.join('[%d]={%s}'%(cmd,','.join('{%s,%d,%d,%d}'%tracks[cmd,p] for p in range(4))) for cmd in sorted({c for c,p in tracks}))+'};')
 # YM2149 odd amplitude steps -> nearest SN76489 2 dB attenuation, 6 dB mix headroom.
 amplitudes=[0,141,222,306,441,585,836,1112,1595,2146,3081,4135,6006,8155,11976,16382]
 levels=[10**(-i/10) for i in range(15)]+[0]
 attenuation=[min(range(16),key=lambda j:abs(levels[j]-a/32764)) for a in amplitudes]
 rows.append('static const u8 sfx_attenuation[16]={'+','.join(map(str,attenuation))+'};')
 (ROOT/'src/sfx_data.inc').write_text('/* Native timed SSG register data. Unbounded captures are excluded. */\n'+'\n'.join(rows)+'\n')
 for bank,pc,raw in [(7,0x88ee,'3e1bcde203'),(7,0x8b74,'3e3acde203'),(7,0x8524,'3e1fcde2033e02cde203')]:s.expect(bank,pc,raw)
 report=dict(source_set=ref['source_set'],commands=sorted({c for c,p in tracks}),profiles=len(tracks),unique_streams=len(unique),bytes=sum(sizes),unsupported=sorted(unsupported),attenuation=attenuation,event_witnesses=list(s.witnesses.values()),scope='34 finite source effects, four timer phases each. Sustained commands 14/3C did not terminate or repeat within capture and are not represented as finite sounds.')
 (ROOT/'reference/sfx.json').write_text(json.dumps(report,indent=2)+'\n');print({k:report[k] for k in ('profiles','unique_streams','bytes','unsupported')})
if __name__=='__main__':generate()
