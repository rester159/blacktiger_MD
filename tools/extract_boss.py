"""Verified damage-layer contract for the two stacked boss constructors."""
def extract(s):
 s.expect(4,0x9ebf,'212ba21140f9016000edb0')
 s.expect(4,0x9f24,'218ba21140f901c000edb0')
 s.expect(4,0xa0b0,'dd3515cad5a0')
 s.expect(4,0xa0c6,'dd360080dd360e10dd362101')
 s.expect(4,0xa0e1,'1e601605cdd003')
 s.expect(4,0xa15c,'cd385ac9')
 s.expect(None,0x5a38,'af3215e93218e93e01322fe0')
 s.expect(4,0x9b97,'dd3515cab99b')
 s.expect(4,0x9bae,'dd360e02dd362101')
 s.expect(4,0x9bca,'1e181605cdd003')
 s.expect(None,0x59bf,'2120f51121f501df083600edb0')
 a=s.read(4,0xa22b,96);b=s.read(4,0xa28b,192)
 return {'source_set':s.lock['aggregate_sha256'],'constructors':[0x9eb1,0x9f16],
         'initial_health':[a[14],b[14]],'layers':[a[21],b[21]],'reset_health':s.read(4,0xa0cd,1)[0],
         'component_counts':[len(a)//48,len(b)//48],
         'upper_health':[a[48+14],b[48+14]],'upper_layers':a[48+21], 'upper_damage':a[48+15],
         'upper_reset_health':s.read(4,0x9bb1,1)[0], 'upper_score':int(''.join(map(str,s.read(None,0x15bc+0x18-7,8)))),
         'score':int(''.join(map(str,s.read(None,0x15bc+0x60-7,8)))),
         'scope':'Damage-layer and reward contract only; multi-part construction, movement, vulnerability and clear presentation require a full native boss implementation.',
         'witnesses':list(s.witnesses.values())}
