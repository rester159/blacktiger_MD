"""Stationary lethal zones and normal player contact dimensions."""
from extract_animation import compile_clip

def extract(s):
 s.expect(1,0xb2b5,'21e6b2012000edb0')
 t=s.read(1,0xb2e6,32)
 assert t[12]==9 and t[13]==39
 handler=s.word(None,0x4751+t[13]*2)
 s.expect(None,handler,'3e403200f43e01321ef4')
 s.expect(None,0x3195,'3a0bf4dd8610b8d8')
 s.expect(None,0x31aa,'3a0cf4dd8611b8d8')
 s.expect(None,0x224e,'3e06cd4b0321ccb11100f4014000edb0')
 player=s.read(6,0xb1cc,64)
 clip=compile_clip(s,1,s.word(1,0xb304)+5)
 return {'source_set':s.lock['aggregate_sha256'],'constructor':0xb2a9,'contact_handler':handler,'half_width':t[16],'half_height':t[17],'player_half_width':player[11],'player_half_height':player[12],'clip':clip,'witnesses':list(s.witnesses.values())}
