"""Compile source effect parameters to typed native operations, never CPU code."""
import hashlib,json
from arcade_source import Source,ROOT

def generate():
 s=Source();b=s.files['bd-06.1l'];rows=[];programs=[];total=0
 for command in [*range(1,31),*range(0x3a,0x40)]:
  ptr=int.from_bytes(b[0xdc1+command*2:0xdc3+command*2],'little');flags=b[ptr];at=ptr+1;ops=[];mark=None;addresses=[]
  assert flags&128
  while True:
   addresses.append(at);op=b[at];at+=1;group=op>>5
   if group==0:
    kind=(op>>2)&7
    if kind==0:value=(op<<8)|b[at];at+=1;ops.append((value,0,0))
    elif kind==1:mark=len(ops);ops.append((0,9,0))
    elif kind==2:
     assert mark is not None;ops.append((mark+1,10,b[at]));at+=1
    else:
     assert kind>=4,'Unsupported source return operation';ops.append((0,11,0));break
   elif group<=3:
    assert not(op&16);value=((op&15)<<8)|b[at];delta=b[at+1];at+=2;ops.append((value,group+1,delta))
   elif group<=6:
    value=op&31;assert value<=15 or value==31;ops.append((value,group+1,b[at]));at+=1
   else:
    value=((op&31)<<8)|(b[at]&56);delta=b[at+1];at+=2;ops.append((value,8,delta))
   assert len(ops)<512
  # Independently resolve the bounded source loop structure into its duration.
  pc=counter=updates=0
  for guard in range(100000):
   value,kind,delta=ops[pc];pc+=1
   if kind==0:updates+=value or 65536
   elif kind==9:counter=0
   elif kind==10:
    counter=(counter+1)&255
    if counter!=delta:pc=value
   elif kind==11:updates+=1;break
  else:raise AssertionError('Unbounded effect program')
  name=f'sfx_program_{command:02x}'
  rows.append('static const SfxOp '+name+'[]={'+','.join('{%d,%d,%d}'%(v,k,d) for v,k,d in ops)+'};')
  total+=len(ops)*4
  programs.append(dict(command=command,flags=flags,ops=len(ops),updates=updates,address=ptr,bytes=at-ptr,source_sha256=hashlib.sha256(b[ptr:at]).hexdigest(),addresses=addresses))
 rows.append('static const SfxTrack sfx_tracks[64]={'+','.join('[%d]={sfx_program_%02x,%d,%d}'%(p['command'],p['command'],p['ops'],p['flags']) for p in programs)+'};')
 # Existing documented YM2149 -> SN76489 attenuation adaptation, 6 dB headroom.
 levels=[10**(-i/10) for i in range(15)]+[0]
 amplitudes=[0,141,222,306,441,585,836,1112,1595,2146,3081,4135,6006,8155,11976,16382]
 attenuation=[min(range(16),key=lambda j:abs(levels[j]-a/32764)) for a in amplitudes]
 rows.append('static const u8 sfx_attenuation[16]={'+','.join(map(str,attenuation))+'};')
 (ROOT/'src/sfx_data.inc').write_text('/* Typed duration, pitch, volume, noise and bounded-loop parameters. */\n'+'\n'.join(rows)+'\n')
 for bank,pc,raw in [(7,0x88ee,'3e1bcde203'),(7,0x8b74,'3e3acde203'),(7,0x8524,'3e1fcde2033e02cde203')]:s.expect(bank,pc,raw)
 report=dict(source_set=s.lock['aggregate_sha256'],commands=[p['command'] for p in programs],programs=programs,bytes=total,unsupported=[],attenuation=attenuation,event_witnesses=list(s.witnesses.values()),scope='All 36 source effect parameter programs compiled to typed operations. Native pitch/volume/noise ramps and bounded repeats replace recorded streams; source observations separately validate behavior.')
 (ROOT/'reference/sfx.json').write_text(json.dumps(report,indent=2)+'\n');print({k:report[k] for k in ('bytes','unsupported')})
if __name__=='__main__':generate()
