"""Production sprite budget helpers match a scalar model at every valid Y."""
import ctypes as C,json,random,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'src/video.c').read_text();start=source.index('static inline u8 sprite_lines_fit');end=source.index('static inline void sprite_entry',start)
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    (tmp/'test.c').write_text('#include <stdint.h>\ntypedef uint8_t u8;typedef uint16_t u16;u8 line_count[28];\n'+source[start:end]+ '\nu8 fit(u16 start,u16 end,u8 units){return sprite_lines_fit(start,end,units);}\nvoid add(u16 start,u16 end,u8 units){sprite_lines_add(start,end,units);}\n')
    subprocess.run(['cc','-shared','-fPIC','-O2',str(tmp/'test.c'),'-o',str(tmp/'test.dylib')],check=True)
    lib=C.CDLL(str(tmp/'test.dylib'));counts=(C.c_uint8*28).in_dll(lib,'line_count');rng=random.Random(1707);checks=0
    for size,units in ((16,1),(32,2)):
        for y in range(-size+1,224):
            first=max(0,y>>3);last=min(28,(y+size+7)>>3)
            assert 1<=last-first<=5
            for trial in range(100):
                before=[rng.randrange(17) for _ in range(28)]
                # Include uniform boundary conditions as well as mixed occupancy.
                if trial<17:before=[trial]*28
                counts[:]=before
                expected=all(v+units<=16 for v in before[first:last])
                assert bool(lib.fit(first,last,units))==expected,(size,y,before)
                assert list(counts)==before
                if expected:
                    lib.add(first,last,units)
                    after=before.copy()
                    for i in range(first,last):after[i]+=units
                    assert list(counts)==after,(size,y,'out-of-band mutation')
                checks+=1
report=dict(passed=True,cases=checks,scope='Production sprite scanline budget helpers; all drawable Y coordinates, both sprite widths, capacity boundaries and deterministic mixed occupancy.')
(ROOT/'reports/sprite-lines-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
