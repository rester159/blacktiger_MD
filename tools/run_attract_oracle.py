"""Witness the arcade's full initial title/ranking/demo pair and coin prompt."""
import gzip,json,hashlib
from arcade_source import Source,ROOT
from oracle_runner import run_oracle
s=Source()
s.expect(None,0x0bb8,'2100b02216e03e013218e0c32413')
s.expect(7,0x8064,'2118e03520112a16e023232216e07e32e8e0237e3218e0')
lines,report=run_oracle(s,'attract-oracle')
p=ROOT/'reports/attract-oracle/full.bin';raw=p.read_bytes();assert len(raw)==5100*5126
rows=[list(map(int,l.split())) for l in (p.parent/'full.tsv').read_text().splitlines()]
assert [(r[0],r[1]) for i,r in enumerate(rows) if i and r[1]!=rows[i-1][1]][:3]==[(151,1),(993,2),(4186,3)]
assert rows[1518][2:4]==[0xb002,35]
(ROOT/'reference/attract_oracle_frames.bin.gz').write_bytes(gzip.compress(raw,mtime=0))
report.update(frames=5100,frame_bytes=5126,frames_sha256=hashlib.sha256(raw).hexdigest(),source_witnesses=list(s.witnesses.values()),demo_input_bank=7,demo_input_address=0xb000,demo_first_input_frame=1519)
(ROOT/'reference/attract_oracle.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
