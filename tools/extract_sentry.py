"""Stationary directional actor (bank 2 B67F) and shared source aiming table."""
from extract_animation import compile_clip

def extract(s):
 t=s.read(2,0xb732,48)
 clips=[compile_clip(s,2,p) for p in (0xb765,0xb76d,0xb775,0xb77d,0xb785,0xb78d,0xb798)]
 for c in clips[:6]:assert c['terminal']=='event' and c['event']['address']==0xb6c0
 assert clips[6]['terminal']=='retire'
 s.expect(2,0xb6c0,'3a09e0fe3f3828cdb205')
 s.expect(2,0xb714,'3e04cde203cde954')
 return {'clips':clips,'aim_table':list(s.read(None,0x688,64)),'health':t[14],'score':int(''.join(map(str,s.read(None,0x15bc+t[23]-7,8)))),'source_set':s.lock['aggregate_sha256']}
