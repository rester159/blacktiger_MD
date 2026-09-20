"""Shared 256-pixel checkpoint grids and source player spawn offset."""
def extract(s):
 s.expect(None,0x2532,'dd2158e03a00e9a7')
 s.expect(None,0x2547,'3aa1f3875f160021b8b2195e2356d5')
 s.expect(None,0x2560,'7ce607878747')
 s.expect(None,0x2570,'7ce60380e187875f160019')
 s.expect(None,0x25a8,'7ce60387878747')
 s.expect(None,0x25b9,'7ce60780e187875f160019')
 grids=[];wide=[]
 for r in range(8):
  pc=s.word(6,0xb2b8+r*2);raw=s.read(6,pc,128)
  grids.append([[int.from_bytes(raw[i:i+2],'big'),int.from_bytes(raw[i+2:i+4],'big')] for i in range(0,128,4)])
  wide.append(int(bool(s.read(6,0xb19c+r*6+4,1)[0])))
 hero=s.read(6,0xb1cc,64)
 return dict(grids=grids,wide=wide,player_offset=[int.from_bytes(hero[1:3],'big'),int.from_bytes(hero[3:5],'big')],source_set=s.lock['aggregate_sha256'],witnesses=list(s.witnesses.values()))
