"""Alternate-area triggers, camera destinations and animated background writes."""
import json,struct
from arcade_source import Source,ROOT

def extract(s):
 s.expect(None,0x4795,'8c4f')
 s.expect(None,0x4f8c,'3a12f4473a18f44f3a16f4b0b1c0')
 s.expect(None,0x6f71,'2a27e97ea7c0cd1204c9')
 s.expect(None,0x6f7d,'21ae6f012000edb0')
 template=s.read(None,0x6fae,32)
 assert template[13]==0x22 and template[16:18]==b'\x06\x06'
 s.expect(None,0x7041,'2a30e084672238e02a32e0223ae0')
 s.expect(None,0x705b,'56235eed5330e02356235eed5332e0')
 s.expect(None,0x7080,'2a38e02230e02a3ae02232e0')
 s.expect(None,0x2aef,'5e23567ab3c8237e1223137e1223c3ef2a')
 rows=[]
 for r in range(8):
  triggers=set();root=s.word(None,0x1e07+2*r)
  for p in struct.unpack('<33H',s.read(5,root,66))[1:]:
   for i in range(128):
    raw=s.read(5,p+i*8,8)
    if raw[:2]==b'\xff\xff':break
    x,y,pc,bank,key=struct.unpack('<HHHBB',raw)
    if pc==0x6f71:triggers.add((x,y,key))
   else:raise AssertionError('spawn list has no terminator')
  animations=[]
  for alternate in (0,1):
   table=s.word(None,0x2b00+16*alternate+2*r);phases=[]
   for phase in range(8):
    p=s.word(4,table+2*phase);writes=[]
    for i in range(1024):
     address=s.word(4,p);p+=2
     if not address:break
     tile=s.word(4,p);p+=2
     assert 0xc000<=address<0xd000 and not address&1
     writes.append({'offset':(phase%4)*4096+address-0xc000,'tile':tile})
    else:raise AssertionError('background list has no terminator')
    phases.append(writes)
   animations.append(phases)
  rows.append(dict(round=r+1,triggers=[dict(x=x,y=y,persistent=k) for x,y,k in sorted(triggers)],camera=list(struct.unpack('<HH',s.read(None,0x7110+4*r,4))),return_x_low_add=s.read(None,0x7130+r,1)[0],background=animations))
 return dict(source_set=s.lock['aggregate_sha256'],rounds=rows,contact_half_size=[6,6],witnesses=list(s.witnesses.values()))
if __name__=='__main__':
 data=extract(Source());(ROOT/'reference/bonus.json').write_text(json.dumps(data,indent=2)+'\n')
 print(json.dumps([dict(round=r['round'],triggers=len(r['triggers']),camera=r['camera'],animation_writes=[sum(map(len,a)) for a in r['background']]) for r in data['rounds']]))
