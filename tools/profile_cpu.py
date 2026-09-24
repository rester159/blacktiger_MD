#!/usr/bin/env python3
"""Instruction-cycle profiler for the pinned ARM64 Genesis Plus GX test core.

Wraps the host core's 68000 opcode dispatch; no instrumentation is inserted into
ROM code and no emulated cycles are added. Per-PC totals are exclusive and include
instruction wait adjustments reported by the core, not all external DMA stalls.
Never load a different core with these internal structure offsets.
"""
import bisect, ctypes as C, hashlib, subprocess
from pathlib import Path
import numpy as np
from run_rom import ROOT, CORE

class CPUProfiler:
    def __init__(self,symbols):
        expected='20903bdbe7dde068ebc55eabb00a2bf45238a254f24fbe2285d12389520dbba0'
        if hashlib.sha256(CORE.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('CPU hook supports only the hash-pinned ARM64 test core')
        source=ROOT/'tools/profile_cpu_hook.c';library=ROOT/'.local/profile_cpu_hook.dylib'
        if not library.exists() or library.stat().st_mtime<source.stat().st_mtime:
            subprocess.run(['cc','-O2','-dynamiclib',str(source),'-o',str(library)],check=True)
        self.lib=C.CDLL(str(library));self.lib.profile_begin.argtypes=[C.c_void_p]*3
        self.symbols=sorted((int(v[0],16),v[2]) for line in symbols.read_text().splitlines() if len(v:=line.split())>=3 and v[1] in ('t','T') and int(v[0],16)<0x400000)
        self.addresses=[v[0] for v in self.symbols]
    def begin(self,r):
        base=C.cast(r.lib.m68k_get_reg,C.c_void_p).value-0x55aac
        cpu=C.addressof(C.c_uint8.in_dll(r.lib,'m68k'))
        if self.lib.profile_begin(cpu,base+0x1fefb0,base+0x1719c0):raise RuntimeError('Cannot install CPU dispatch hook')
    def end(self):
        self.lib.profile_end()
        hist=np.ctypeslib.as_array((C.c_uint64*0x200000).in_dll(self.lib,'instruction_cycles'))
        counts={}
        for index in np.nonzero(hist)[0]:
            slot=bisect.bisect_right(self.addresses,int(index)*2)-1
            name=self.symbols[slot][1] if slot>=0 else 'vectors'
            counts[name]=counts.get(name,0)+int(hist[index])
        total=sum(counts.values())
        return dict(attributed_master_cycles=total,functions=[dict(name=k,percent=round(v/total*100,3),master_cycles=v) for k,v in sorted(counts.items(),key=lambda x:-x[1])],hot_pcs=[dict(pc=hex(int(i)*2),master_cycles=int(hist[i])) for i in np.argsort(hist)[-40:][::-1]])
