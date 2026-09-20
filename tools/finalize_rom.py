#!/usr/bin/env python3
"""Set exact cartridge extent and standard big-endian Genesis checksum after padding."""
from pathlib import Path
import sys
p=Path(sys.argv[1]);b=bytearray(p.read_bytes());assert b[0x100:0x104]==b'SEGA' and len(b)%2==0
b[0x1a4:0x1a8]=(len(b)-1).to_bytes(4,'big')
b[0x18e:0x190]=(sum(int.from_bytes(b[i:i+2],'big') for i in range(0x200,len(b),2))&65535).to_bytes(2,'big')
p.write_bytes(b)
