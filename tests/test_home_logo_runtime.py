"""Home selection adds the approved MD; Arcade and the mode picker stay original."""
import hashlib,json
import numpy as np
from PIL import Image
from test_runtime import ROOT,Runner,state
r=Runner(ROOT/'out/release/rom.bin');r.run(100)
def tap(key):r.run(12,key);r.run(12)
def shot(name):Image.fromarray(r.frame).save(ROOT/'screenshots'/name)
original=r.frame.copy();shot('00_main_title.png')
stamp=original[216:224,232:248].copy();assert np.count_nonzero(stamp)>30,'Version missing on main menu'
tap(8);arcade=r.frame.copy();tap(1)
tap(32);tap(8)
assert list(r.read('frontend',3))==[1,1,0]
home=r.frame.copy();shot('home_title.png')
assert np.array_equal(home[216:224,232:248],stamp),'Version missing on Home'
assert np.array_equal(original[24:104],home[24:104]),'Original wordmark changed'
assert not np.array_equal(original[104:136,96:160],home[104:136,96:160]),'Missing MD'
assert np.count_nonzero(home[104:136,96:160])>500,'MD is blank'
# Logo tiles stay on BG_B while menu navigation updates only BG_A.
tap(32);tap(32);tap(8);assert r.read('frontend',2)==bytes([1,2])
tap(1);assert r.read('frontend',2)==bytes([1,1])
assert np.array_equal(home[24:136],r.frame[24:136]),'Home options return lost MD'
tap(1);assert r.read('frontend',2)==bytes([1,0])
assert np.array_equal(original[24:136],r.frame[24:136]),'MD leaked into mode picker'
tap(16);tap(8);assert r.read('frontend',2)==bytes([0,1])
assert np.array_equal(arcade[24:136],r.frame[24:136]),'MD leaked into Arcade'
assert np.array_equal(r.frame[216:224,232:248],stamp),'Version missing on Arcade'
shot('arcade_title.png')
r.close()
report=dict(passed=True,rom_sha256=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest(),home_only=True,version_on_all_three_menus=True,original_wordmark_unchanged=True,options_return=True,arcade_restored=True,scope='Actual ROM screenshots through controller-driven Home, Options, mode-picker and Arcade transitions. The approved MD alone is reduced to 64x32 using existing title palettes; original wordmark pixels remain unchanged.')
(ROOT/'reports/home-logo-runtime-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
