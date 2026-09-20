"""Validate development source evidence; deliberately not a native-port test."""
import hashlib,json
from arcade_source import Source,ROOT
from extract_thrower import extract
s=Source();contract=json.loads((ROOT/'reference/thrower.json').read_text());assert extract(s)==contract
ref=json.loads((ROOT/'reference/thrower_oracle.json').read_text());assert ref['source_set']==s.lock['aggregate_sha256']
for key,path in [('trace_sha256','reference/thrower_oracle_events.txt'),('lua_sha256','tools/thrower_oracle.lua')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
rows={i:[] for i in range(len(ref['cases']))}
for line in (ROOT/'reference/thrower_oracle_events.txt').read_text().splitlines():
 if line=='COMPLETE':continue
 tag,case,tick,actor,display,small,persist=line.split('|');assert tag=='TICK'
 a=bytes.fromhex(actor);assert len(a)==48 and len(bytes.fromhex(display))==16
 # Small pool also contains drops after death; distinguish the damaging projectile.
 projectiles=[]
 for entry in filter(None,small.split(',')):
  addr,data=entry.split(':');w=bytes.fromhex(data);assert 0xf520<=int(addr,16)<0xf940 and len(w)==32
  if w[13]&127==0:projectiles.append(w)
 rows[int(case)].append((int(tick),a,projectiles))
summary=[]
for i,c in enumerate(ref['cases']):
 data=rows[i];assert [t for t,a,p in data]==list(range(1,c['ticks']+1))
 first_throw=next((t for t,a,p in data if a[33]),None)
 if c['name'].startswith('emerge_throw'):assert first_throw==145 and any(a[7]>=128 for t,a,p in data)
 if c['name'].startswith('walk_'):assert first_throw is None and not any(p for t,a,p in data)
 if c['hit_tick']:
  assert data[c['hit_tick']-1][1][14]==3,'Nonfatal hit must leave three health'
  assert data[c['hit2_tick']-1][1][0]==64,'Second hit must enter death'
  assert data[-1][1][0]==0,'Death must retire'
 projectile_frames=sum(bool(p) for t,a,p in data)
 for t,a,projectiles in data:
  for w in projectiles:assert tuple(w[15:18])==(1,8,4)
 summary.append({'case':c['name'],'ticks':len(data),'first_throw_tick':first_throw,'projectile_frames':projectile_frames,'upward_motion_ticks':sum(a[7]>=128 for t,a,p in data)})
report={'source_evidence_verified':True,'native_implementation_complete':False,'source_ticks':sum(len(v) for v in rows.values()),'typed_segments':len(contract['segments']),'cases':summary,'next_implementation':'Extend the recurring walker with a variant profile, throw-once state, jump callbacks, and independently retiring/damageable projectiles. Preserve projectile lifetime after parent death and source family-specific spawn positions/cap.'}
(ROOT/'reports/thrower-source-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
