"""Compile armor fragments through the shared native animation format."""
from arcade_source import Source,ROOT
from extract_animation import compile_clip
import json
def generate(s):
 s.expect(None,0x7a09,'cdf3253e17cde203af32adf3')
 clips=[];rows=['/* Generated source armor fragment data. */']
 for i in range(4):
  t=s.read(None,0x7a6b+i*32,32);assert t[0]==128 and t[10]==1
  c=compile_clip(s,None,int.from_bytes(t[30:32],'little')+5);clips.append(c)
  assert c['terminal']=='loop' and len(c['frames'])==8 and c['loop']==4
  rows.append('static const AnimFrame armor_frames_%d[]={%s};'%(i,','.join('{%d,%d,%d,%d,0,%d,%d}'%(f['code'],f['duration'],f['palette'],f['flip'],f['vx'],f['vy']) for f in c['frames'])))
 rows.append('static const AnimClip armor_clips[4]={'+','.join('{armor_frames_%d,8,4}'%i for i in range(4))+'};')
 (ROOT/'src/armor_break_data.inc').write_text('\n'.join(rows)+'\n')
 (ROOT/'reference/armor_break.json').write_text(json.dumps(dict(clips=clips,witnesses=list(s.witnesses.values())),indent=2)+'\n')
if __name__=='__main__':generate(Source())
