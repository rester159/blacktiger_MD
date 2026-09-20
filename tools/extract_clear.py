"""Compile captured victory frames and source Zenny awards into native data."""
import json,hashlib
from arcade_source import Source,ROOT

def generate(s):
 ref=json.loads((ROOT/'reference/clear_oracle.json').read_text())
 assert ref['source_set']==s.lock['aggregate_sha256']
 for key,path in [('trace_sha256','reference/clear_oracle_events.txt'),('lua_sha256','tools/clear_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
 frames={};ends={};rewards=[]
 for line in (ROOT/'reference/clear_oracle_events.txt').read_text().splitlines():
  f=line.split('|')
  if f[0]=='FRAME':frames.setdefault(int(f[1]),[]).append(dict(tick=int(f[2]),ticks=int(f[3]),armor=int(f[4]),raw=bytes.fromhex(f[5]+f[6])))
  elif f[0]=='END':ends[int(f[1])]=int(f[2])
  elif f[0]=='REWARD':rewards.append((int(f[1]),int(f[2]),int(''.join(str(v) for v in bytes.fromhex(f[3])))))
 s.expect(None,0x5bc4,'ca987b')
 s.expect(None,0x5cd2,'211a5e197ecdaf4f')
 s.expect(None,0x5ce1,'21225e195e23562aa7f31922a7f3')
 s.expect(None,0x5cf4,'cd2c03');s.expect(None,0x032c,'3ef0')
 coins=[]
 for r in range(8):
  amount=s.word(None,0x5e22+2*r);index=s.read(None,0x5e1a+r,1)[0]
  assert int(''.join(map(str,s.read(None,0x505e+index-4,5))))==amount
  coins.append(amount if r<7 else 0)
 for i,binary,display in rewards:
  c=ref['cases'][i];amount=s.word(None,0x5e22+2*c['round'])
  assert binary==(c['coins']+amount)&65535 and display==(c['coins']+amount)%100000
 rows=[];profiles=[]
 for i in range(10):
  ordinary=frames[i];ending=frames[i+10];assert ordinary[:len(ending)]==ending
  cooked=[]
  for j,f in enumerate(ordinary):
   sprites=[];mask=0
   for k in range(6):
    code,attr,y,x=f['raw'][k*4:k*4+4]
    if y:mask|=1<<k
    sprites.append(dict(code=code|((attr&224)<<3),palette=attr&7,flip=(attr>>3)&1,dx=(x-112)&255,dy=(y-144)&255))
   cooked.append(dict(ticks=f['ticks'],sprites=sprites,visible=mask,hold=int(i%2==0 and j==0)))
  name='clear_frames_'+str(i)
  rows.append('static const ClearFrame '+name+'[]={'+','.join('{'+str(f['ticks'])+','+str(f['visible'])+','+str(f['hold'])+',{' + ','.join('{'+','.join(str(p[k]) for k in ('code','palette','flip','dx','dy'))+'}' for p in f['sprites'])+'}}' for f in cooked)+'};')
  profiles.append('{'+name+','+str(len(ordinary))+','+str(len(ending))+'}')
 rows.append('static const ClearClip clear_clips[10]={'+','.join(profiles)+'};')
 rows.append('static const u16 clear_coins[8]={'+','.join(map(str,coins))+'};')
 (ROOT/'src/round_clear_data.inc').write_text('/* Source-derived sprite data and rewards; native control flow. */\n'+'\n'.join(rows)+'\n')
 data=dict(coins=coins,bonus_ticks=240,durations=[ends[i] for i in range(20)],source_set=s.lock['aggregate_sha256'],witnesses=list(s.witnesses.values()))
 (ROOT/'reference/round_clear.json').write_text(json.dumps(data,indent=2)+'\n');return data
if __name__=='__main__':print(generate(Source()))
