"""Compile observed rescue presentation into shared native pages and timelines."""
import hashlib,json
import numpy as np
from arcade_source import ROOT

def generate(source,emit,decode,pack,words):
 ref=json.loads((ROOT/'reference/npc_sequence_oracle.json').read_text())
 for key,path in [('trace_sha256','reference/npc_sequence_oracle_events.txt'),('lua_sha256','tools/npc_sequence_oracle.lua')]:
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref[key]
 assert ref['source_set']==source.lock['aggregate_sha256']
 records=[l.split('|') for l in (ROOT/'reference/npc_sequence_oracle_events.txt').read_text().splitlines() if l!='COMPLETE']
 pages=[tuple([32]*128)];timelines=[];durations=[]
 for kind in range(1,9):
  rows=[(tag,*map(int,f)) for tag,*f in records if int(f[0])==kind];events=[];cells=list(pages[0]);i=0
  while i<len(rows):
   tag,k,tick,a,b=rows[i];i+=1
   if tag=='WAIT':continue
   if tag in ('TEXT','ATTR'):
    def put(tag,a,b):
     cell=a-256
     cells[cell]=(cells[cell]&0x700)|b if tag=='TEXT' else (cells[cell]&255)|((b&224)<<3)
    put(tag,a,b)
    while i<len(rows) and rows[i][0] in ('TEXT','ATTR') and rows[i][2]==tick:
     tag,_,_,a,b=rows[i];put(tag,a,b);i+=1
    page=tuple(cells)
    if page not in pages:pages.append(page)
    events.append((tick,pages.index(page),1))
   else:events.append((tick,a,{'SPRITE':0,'SOUND':2,'REWARD':3,'END':4}[tag]))
  assert events[-1][2]==4;durations.append(events[-1][0]);timelines.append(events)
 used=sorted(set(c for page in pages for c in page));board=json.loads((ROOT/'assets/board.json').read_text())
 chars=decode(b''.join(source.files[f['path']] for f in board['regions']['chars']['files']),board['layouts']['characters'])
 font=bytearray();dedup={};glyphs=[0]*2048
 for char in used:
  # Adapt source pens to existing black, white and gray object-palette pens.
  # Source pen 3 is transparent; pen 0 supplies the opaque dialogue backdrop.
  raw=pack(np.array([1,15,6,0],dtype=np.uint8)[chars[char]])
  if raw not in dedup:dedup[raw]=len(dedup);font.extend(raw)
  slot=dedup[raw];tile=1408+slot if slot<32 else 1072+slot-32 if slot<48 else 1+slot-48
  glyphs[char]=tile|(3<<13)|0x8000
 assert len(dedup)<=63
 emit('npc_dialogue_font',bytes(font),'u32');emit('npc_dialogue_glyphs',words(glyphs))
 text='/* Source-derived typed rescue events. No arcade instructions. */\n'
 text+='static const u16 npc_pages[][128]={'+','.join('{'+','.join(map(str,p))+'}' for p in pages)+'};\n'
 for i,events in enumerate(timelines):text+='static const NpcEvent npc_events_'+str(i)+'[]={'+','.join('{'+','.join(map(str,e))+'}' for e in events)+'};\n'
 text+='static const NpcEvent *const npc_events[8]={'+','.join('npc_events_'+str(i) for i in range(8))+'};\n'
 (ROOT/'src/npc_sequence_data.inc').write_text(text)
 (ROOT/'src/npc_sequence_visual.inc').write_text('#define NPC_FONT_TILES '+str(len(dedup))+'\n')
 report=dict(source_set=ref['source_set'],durations=durations,pages=len(pages),font_tiles=len(dedup),events=[len(e) for e in timelines],scope='Original task-relative body frames, text cells, pauses, sound commands, rewards and terminal branches. Native glyphs adapt to existing black/white/gray object-palette pens; scheduler/task deletion and HUD refresh were bypassed in the oracle.')
 (ROOT/'reference/npc_sequence.json').write_text(json.dumps(report,indent=2)+'\n');return report
