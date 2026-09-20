"""Falling/bouncing boulder, bank 4 B338: typed data for native event handlers."""
from extract_animation import compile_clip
ROOTS=[0xb470,0xb47b,0xb486,0xb491,0xb49c]
EVENTS=[0xb375,0xb3aa,0xb430]
def extract(s):
 s.expect(None,0x3246,'1605dd5e17c3d003')
 s.expect(4,0xb344,'2140b4013000edb0')
 s.expect(4,0xb3bf,'113000')
 s.expect(4,0xb3f6,'dd360f02dd3607fddd361200dd360601')
 template=s.read(4,0xb440,48);segments=[];pending=[];indices={}
 def intern(pc):
  if pc not in indices:indices[pc]=len(segments);segments.append(None);pending.append(pc)
  return indices[pc]
 roots=list(map(intern,ROOTS))
 while pending:
  pc=pending.pop(0);clip=compile_clip(s,4,pc);event=3;targets=[65535,65535]
  assert clip['terminal'] in ('retire','event')
  if clip['terminal']=='event':
   e=clip['event'];event=EVENTS.index(e['address']);targets[0]=intern(e['record']+3)
   if event==1:targets[1]=intern(e['record']+6)
   if event==0:targets[1]=roots[1]
  segments[indices[pc]]={'source':pc,'clip':clip,'event':event,'next':targets}
 return {'source_set':s.lock['aggregate_sha256'],'roots':roots,'segments':segments,'weapon_score':int(''.join(map(str,s.read(None,0x15bc+template[23]-7,8)))),'health':template[14],'damage':template[15],'bounce_damage':s.read(4,0xb3f9,1)[0],'witnesses':list(s.witnesses.values())}
