"""Shared emerge/hide enemy variants at bank 2 8000/81A2."""
from extract_animation import compile_clip

def extract(s):
 profiles=[]
 for offset in (0,0x1a2):
  t=s.read(2,0x80c6+offset,48)
  roots=[p+offset for p in (0x80f6,0x8108,0x8115,0x8122,0x8137,0x816f)]
  clips=[compile_clip(s,2,p) for p in roots]
  assert [c['terminal'] for c in clips]==['event','event','event','retire','event','retire']
  assert [clips[i]['event']['address'] for i in (0,1,2,4)]==[p+offset for p in (0x806c,0x8090,0x807c,0x807c)]
  s.expect(2,0x8006+offset,'23237ea728082b7efe1e281934c9')
  s.expect(2,0x8014+offset,'2a23e93a02f4c64095fe80d0')
  s.expect(2,0x8020+offset,'2a27e9237efe03280234c9')
  profiles.append({'constructor':0x8000+offset,'health':t[14],'width':t[16],'height':t[17],'score':int(''.join(map(str,s.read(None,0x15bc+t[23]-7,8)))),'clips':clips})
 s.expect(None,0x3434,'3a03e00fd0')
 s.expect(None,0x34f4,'3a02f4dd96023002ed44473a0bf4dd8610b8d8')
 s.expect(None,0x47e5,'3e013208e93e15cde203c31c48')
 return {'source_set':s.lock['aggregate_sha256'],'profiles':profiles,'witnesses':list(s.witnesses.values())}
