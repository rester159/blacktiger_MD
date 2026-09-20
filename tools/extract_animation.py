"""Compile source animation DATA into typed native frames, with explicit event boundaries.
All common animation loaders consume exactly five bytes. 00/FF/FE records dispatch a
behavior callback, jump to another frame, or retire an actor. These are resolved offline;
no ROM pointers, original instructions, or CPU state enter the native runtime.
"""
from arcade_source import Source,ROOT
import json

def compile_clip(source,bank,start):
 frames=[];addresses={};pc=start
 while len(frames)<256:
  if pc in addresses:return {'frames':frames,'loop':addresses[pc],'terminal':'loop','event':None}
  marker=source.read(bank,pc,1)[0]
  if marker==255:
   pc=source.word(bank,pc+1)
   # The loader reads one jump then assumes an ordinary frame, so reject chains.
   assert source.read(bank,pc,1)[0] not in (0,254,255),('invalid animation jump',bank,hex(pc))
   continue
  if marker==254:return {'frames':frames,'loop':None,'terminal':'retire','event':None}
  if marker==0:return {'frames':frames,'loop':None,'terminal':'event','event':{'bank':bank,'address':source.word(bank,pc+1),'record':pc}}
  addresses[pc]=len(frames);duration,base,attr,vx,vy=source.read(bank,pc,5)
  frames.append({'duration':duration,'code':base|((attr&224)<<3),'palette':attr&7,'flip':bool(attr&8),
    'vx':None if vx==128 else vx if vx<128 else vx-256,
    # Source 303C jumps past BOTH velocity writes when vx==80.
    'vy':None if vx==128 or vy==128 else vy if vy<128 else vy-256,
    'source_address':pc})
  pc+=5
 raise ValueError('unterminated clip')

def extract(source):
 # Fixed small/medium/large renderers all advance five bytes; sentinels share semantics.
 for pc in (0x3002,0x32e2,0x3667,0x3da7):source.expect(None,pc,'11050019')
 source.expect(None,0x3039,'7efe80280cdd7706237efe802803dd7707')
 # The shared statue constructor installs this exact template.
 source.expect(None,0x5ed1,'21315f013000edb0')
 t=source.read(None,0x5f31,48);assert t[10]==1 and int.from_bytes(t[30:32],'little')==0x5f5c
 variants=[]
 for index in range(8):
  pc=0x5e32+18*index;b=source.read(None,pc,27 if index==7 else 18)
  if index==7:
   assert b[6:15]==bytes.fromhex('237ea7280235c93608')
   b=b[:6]+b[15:]
  assert b[:13]==bytes.fromhex('2a27e97ea7c0cdcb5edd360b')+bytes([0x21+index])
  assert b[13:]==bytes.fromhex('dd360d')+bytes([0x2c+index,0xc9])
  variants.append({'constructor':pc,'kind':index,'category':0x21+index,'contact_event':0x2c+index})
 source.expect(None,0x5fc2,'dd7e0bd62121cd5fc30804')
 reward_targets=[source.word(None,0x5fcd+2*i) for i in range(8)]
 assert reward_targets==[0x5fdd,0x6008,0x6025,0x604b,0x6078,0x6097,0x60a8,0x6008]
 source.expect(None,0x5ff1,'2aa7f31164001922a7f3')
 source.expect(None,0x6039,'3ab6f3320ef4af3221f4')
 source.expect(None,0x6064,'1130002ab1f3197dd6603802246f22b1f3')
 source.expect(None,0x5f02,'dd7e0bfe28280add6e18dd66193e02b677')
 idle=compile_clip(source,None,0x5f61);released=compile_clip(source,None,0x5f6c)
 assert idle['terminal']=='loop' and len(idle['frames'])==1 and idle['frames'][0]['code']==0x300
 assert released['terminal']=='retire' and released['frames'][0]['code']==0x304
 # Petrification/rescue cutscene is declarative (body base, wait ticks), not an actor clip.
 cutscene=[];pc=0x60ef
 while True:
  base=source.read(None,pc,1)[0];pc+=1
  if base==0x40:break
  if base==0x2f:cutscene.append({'event':'thanks'});continue
  ticks=source.read(None,pc,1)[0];pc+=1;cutscene.append({'code':0x300|base,'ticks':ticks})
 return {'schema':1,'source_set':source.lock['aggregate_sha256'],'shared_format':{'stride':5,'duration_domain':[1,253],'velocity_hold':128,'hold_x_also_holds_y':True},'npc':{'variants':variants,'template':t.hex(),'idle':idle,'released':released,'rescue_cutscene':cutscene,'rewards':['coins_100','shop','heal','time_30','hint_0','hint_1','hint_2','shop_repeatable']},'witnesses':list(source.witnesses.values())}
if __name__=='__main__':
 result=extract(Source());(ROOT/'reference/animation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['npc'],indent=2))
