#!/usr/bin/env python3
import json
from arcade_source import Source,ROOT
from extract_loot import extract
from oracle_runner import run_oracle
s=Source();d=extract(s);cases=[]
for k in range(1,8):
 cat,sample=next((i,j) for i,row in enumerate(d['tables']) for j,v in enumerate(row) if v==k)
 cases.append((cat,sample))
lines,report=run_oracle(s,'loot-oracle','return {'+','.join('{category=%d,sample=%d}'%c for c in cases)+'}\n')
counts={}
for line in lines:
 v=line.split('|');counts[v[0]]=counts.get(v[0],0)+1
 if v[0]=='DROP':
  category,sample=int(v[1]),int(v[2]);a=bytes.fromhex(v[3]);kind=d['tables'][category][sample]
  if not kind:assert not any(a)
  else:
   t=bytearray.fromhex(d['kinds'][kind-1]['template']);t[1:5]=bytes.fromhex('00580050');t[26:28]=bytes.fromhex('fe28');assert a==t,(category,sample)
 elif v[0]=='COINS':assert int.from_bytes(bytes.fromhex(v[2]),'little')==123+d['kinds'][int(v[1])-1]['coins']
 elif v[0]=='RNG':assert int.from_bytes(bytes.fromhex(v[3]),'little')==int(v[1])*pow(259,int(v[2]),65536)%65536
 elif v[0]=='FULL':assert v[1]=='80'+'00'*31
report.update(passed=True,counts=counts,cases=cases,scope='Every category/sample drop selection, all seven pickup animations and coin rewards, full-pool refusal, and random recurrence. Shared-pool competition and exact player contact bounds remain separate.')
(ROOT/'reports/loot-oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(counts))
