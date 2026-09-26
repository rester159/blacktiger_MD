"""Development-only, checked ROM data access. Never linked into the cartridge."""
from pathlib import Path
import hashlib,json,os
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'assets/source/arcade'
class Source:
 def __init__(self,root=None):
  self.root=Path(root or os.environ.get('BLACKTIGER_SOURCE',DEFAULT)).expanduser().resolve()
  self.lock=json.loads((ROOT/'assets/rom_manifest.json').read_text());self.files={};self.witnesses={}
  for row in self.lock['files']:
   path=self.root/'payload'/row['path']
   if not path.is_file():
    raise ValueError('Original Black Tiger ROM set required. Run: python3 tools/import_rom.py /path/to/blktiger.zip (missing '+row['path']+')')
   raw=path.read_bytes()
   if len(raw)!=row['size'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
    raise ValueError('Wrong ROM revision or damaged file: '+row['path'])
   self.files[row['path']]=raw
 def locate(self,bank,pc,n):
  if pc<0x8000:name='bdu-01a.5e';offset=pc;assert pc+n<=0x8000
  else:
   assert bank is not None and 0<=bank<16 and pc+n<=0xc000
   name=('bdu-02a.6e','bdu-03a.8e','bd-04.9e','bd-05.10e')[bank//4];offset=(bank%4)*0x4000+pc-0x8000
  return name,offset
 def read(self,bank,pc,n):
  name,offset=self.locate(bank,pc,n);raw=self.files[name][offset:offset+n];assert len(raw)==n
  self.witnesses[(name,offset,n)]={'file':name,'offset':offset,'bank':bank if pc>=0x8000 else None,'address':pc,'bytes':raw.hex(),'sha256':hashlib.sha256(raw).hexdigest()}
  return raw
 def word(self,bank,pc):return int.from_bytes(self.read(bank,pc,2),'little')
 def expect(self,bank,pc,data):
  assert self.read(bank,pc,len(bytes.fromhex(data)))==bytes.fromhex(data),(bank,hex(pc),'source contract')

if __name__=='__main__':
 import sys
 try:
  source=Source()
 except (ValueError,OSError) as error:
  sys.exit(str(error))
 print('Verified original Black Tiger ROM set ('+str(len(source.files))+' files).')
