"""Initial resources and score-based maximum vitality."""
def extract(s):
 s.expect(None,0x11f2,'2140e91141e901bf143600edb0')
 s.expect(None,0x1214,'3e0132d6f332f6f3')
 s.expect(None,0x2269,'3ab6f3320ef4')
 s.expect(None,0x22ef,'2aa7f311c8001922a7f33e0232adf3')
 s.expect(None,0x1587,'3ab6f33c32b6f3')
 s.expect(None,0x15aa,'2ab4f31108001922b4f3')
 s.expect(None,0x201c,'af3205e93215e93218e93207e93208e93228e0')
 s.expect(None,0x2038,'3e0232adf3')
 s.expect(None,0x209d,'21a0f335c2e221')
 s.expect(None,0x21e5,'21a0f3dde5d1012000edb0')
 s.expect(None,0x2213,'06c07ef601ee011223137e1223137e1223137e12231310ea')
 s.expect(None,0x2118,'3a25e032a0f3')
 s.expect(None,0x2124,'21e8e111e9e10107003600edb0')
 thresholds=[int(''.join(map(str,s.read(None,0x13be+8*i,8)))) for i in range(4)]
 return dict(thresholds=thresholds,initial_health=s.read(None,0x1215,1)[0],initial_coins=s.word(None,0x22f3),initial_armor=s.read(None,0x22fa,1)[0],source_set=s.lock['aggregate_sha256'],witnesses=list(s.witnesses.values()))
