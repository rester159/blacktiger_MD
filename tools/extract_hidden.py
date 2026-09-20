"""Source-owned hidden terrain, reveal clips, and contact reward dispatch."""
from arcade_source import Source,ROOT
from extract_animation import compile_clip
import json

def extract(s):
 s.expect(2,0xb939,'dd7e08d62947878787906f260019')
 s.expect(2,0xb947,'7ecd6f03235e2356237e1223137e12')
 s.expect(2,0xb956,'e5211f0019ebe1237e1223137e12')
 s.expect(None,0x36f,'32e6e0d30dc9')
 s.expect(2,0xb96d,'3e09dd770cdd6e18dd66193e02b677')
 s.expect(None,0x4744,'dd7e0df680ee80215147c30804')
 kinds=[]
 rewards=[('empty',0),('life',1),('armor_heal',2),('screen_attack',200),('time',30),('coins',1000),('armor',2),('armor',3),('score',1000),('score',5000),('coins',500),('score',7000)]
 for k in range(12):
  pc=0xb7da+k*23;b=s.read(2,pc,23)
  assert b[:13]==bytes.fromhex('2a27e97ea7c0cdeeb8dd360d')+bytes([22+k])
  assert b[13]==0x21 and b[16:]==bytes.fromhex('dd751cdd741dc9')
  cursor=int.from_bytes(b[14:16],'little');s.expect(2,cursor+5,'002bb9')
  clip=compile_clip(s,2,cursor+8);assert clip['terminal']=='loop'
  kinds.append({'kind':k,'constructor':pc,'contact':22+k,'handler':s.word(None,0x4751+(22+k)*2),'clip':clip,'reward':rewards[k][0],'amount':rewards[k][1]})
 for idx,amount in [(0x70,1000),(0x90,5000),(0x98,7000)]:
  digits=s.read(None,0x15bc+idx-7,8);assert all(x<10 for x in digits)
  assert int(''.join(map(str,digits)))==amount
 rounds=[]
 for r in range(8):
  layout=s.read(6,0xb19c+r*6,6)[4];w,h=(128,64) if layout else (64,128)
  inverse={((x&15)|((y&15)<<4)|((x&(0x70 if layout else 0x30))<<4)|((y&(0x30 if layout else 0x70))<<(7 if layout else 6))):(x,y) for y in range(h) for x in range(w)}
  start=s.word(2,0xbb1b+r*2);end=s.word(2,0xbb1d+r*2) if r<7 else 0xbc3c
  assert (end-start)%7==0
  patches=[]
  for n,pc in enumerate(range(start,end,7)):
   b=s.read(2,pc,7);address=int.from_bytes(b[1:3],'little');offset=b[0]*4096+address-0xc000
   assert offset%2==0;xy=[inverse[offset//2],inverse[(offset+32)//2]]
   assert xy[1]==(xy[0][0],xy[0][1]+1) and b[3:]==bytes.fromhex('00300030')
   patches.append({'persistent':41+n,'bank':b[0],'address':address,'cell':xy[0][1]*w+xy[0][0],'x':xy[0][0]*16,'y':xy[0][1]*16,'tiles':[[0,48],[0,48]]})
  rounds.append(patches)
 return {'source_set':s.lock['aggregate_sha256'],'kinds':kinds,'rounds':rounds,'life_collected':compile_clip(s,2,0xbaf0),'explosion':compile_clip(s,2,0xbaf7),'witnesses':list(s.witnesses.values())}
if __name__=='__main__':
 d=extract(Source());(ROOT/'reference/hidden.json').write_text(json.dumps(d,indent=2)+'\n');print('patches',sum(map(len,d['rounds'])))
