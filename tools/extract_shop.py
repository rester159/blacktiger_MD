"""Native shop catalog from fixed purchase dispatch and price tables."""
def extract(s):
 s.expect(None,0x12e8,'db042fe61c0f0f3222e0')
 s.expect(None,0x674c,'3aabf3fe63')
 s.expect(None,0x6753,'2aa7f3111e00')
 s.expect(None,0x6787,'3ab0f3fe63')
 s.expect(None,0x678e,'2aa7f3119600')
 grid=list(s.read(None,0x6e75,12));assert grid==[1,2,3,4,9,0,5,6,7,8,10,11]
 prices=[[[s.word(None,table+10*d+2*t) for t in range(1,5)] for d in range(8)] for table in (0x6e81,0x6ed1)]
 return dict(prices=prices,grid=grid,key_price=s.word(None,0x6757),antidote_price=s.word(None,0x6792),source_set=s.lock['aggregate_sha256'],witnesses=list(s.witnesses.values()))
