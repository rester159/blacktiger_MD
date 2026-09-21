"""M0: freeze a four-line palette budget, with no newly authored graphics."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAMPS=[[0x006,0x00a,0x00e],[0xe60,0xea2,0xec4],[0x806,0xc0a,0xe0e],[0x888,0xccc,0xeee],[0x040,0x080,0x0e0]]
BIOMES=[('GREY STONE',0x222,0xccc),('FROZEN HOLLOW',0xe84,0xeee),('EMERALD GROTTO',0x020,0x8e8),('BONE CATHEDRAL',0x468,0xeee),('DROWNED VAULT',0x600,0xec8),('EMBER DEEP',0x002,0x08e),('RUST WORKS',0x024,0x8ce),('VIOLET SANCTUM',0x402,0xe8e),('GILDED HALL',0x024,0xaee),('THE VOID',0,0x888)]
def rgb(w):return tuple((w>>i)&7 for i in (1,5,9))
def word(c):return sum(v<<i for v,i in zip(c,(1,5,9)))
def distance(a,b):return sum(abs(x-y) for x,y in zip(rgb(a),rgb(b)))
colors=[word((r,g,b)) for b in range(8) for g in range(8) for r in range(8)]
safe=[c for c in colors if all(distance(c,a)>=2 for ramp in RAMPS for a in ramp)]
def nearest(c):return min(safe,key=lambda v:(sum((a-b)**2 for a,b in zip(rgb(v),rgb(c))),v))
biomes=[]
for name,lo,hi in BIOMES:
 ramp=[0]+[nearest(word(tuple((a*(14-i)+b*i+7)//14 for a,b in zip(rgb(lo),rgb(hi))))) for i in range(15)]
 assert all(distance(c,a)>=2 for c in ramp[1:] for affix in RAMPS for a in affix)
 biomes.append(ramp)
# P1 armor 1..4; P2 armor 5..8; shared flail 9..11, dagger 12..13, pickups 14..15.
palette=[*biomes[0],0,0x222,0x444,0x666,0x888,0xaaa,0xccc,0xeee,0x00e,0x0e0,0xe00,0x0ee,0xee0,0xeee,0xeee,0x00e,
 0,0x024,0x048,0x08c,0x0ce,0x420,0x840,0xc80,0xec0,0x666,0xaaa,0xeee,0x888,0xccc,0x0ee,0xeee,
 0,0x222,0x444,0x666,0x888,0xaaa,0xccc,0xeee,*RAMPS[0],*RAMPS[1],0,0]
assert len(palette)==64 and all(not c&0xf111 for c in palette)
assert palette[30:32]==[0xeee,0x00e]
mask=(1<<30)|(1<<31)
lines=['/* Generated M0 palette budget. Palette-3 operator pens 14/15 are not colors. */',
 'static const u16 dungeon_base_palette[64]={'+','.join(hex(v) for v in palette)+'};',
 'static const u16 dungeon_biome_palettes[10][16]={'+','.join('{'+','.join(hex(v) for v in row)+'}' for row in biomes)+'};',
 'static const u16 dungeon_affix_ramps[5][3]={'+','.join('{'+','.join(hex(v) for v in row)+'}' for row in RAMPS)+'};',
 'static const u16 dungeon_safe_colors[512]={'+','.join(hex(nearest(c)) for c in colors)+'};']
(ROOT/'src/dungeon_palette_data.inc').write_text('\n'.join(lines)+'\n')
report=dict(passed=True,palette_lines=4,entries_per_line=16,clock_indices=[30,31],clock_values=palette[30:32],enemy_base=list(range(1,8)),affix_slots=[[8,9,10],[11,12,13]],operators=[14,15],biome_affix_comparisons=10*15*15,minimum_manhattan_distance=min(distance(c,a) for b in biomes for c in b[1:] for ramp in RAMPS for a in ramp),new_image_assets=0)
(ROOT/'reports/dungeon-palette-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
