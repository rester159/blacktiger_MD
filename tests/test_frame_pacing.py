"""Combat clock must keep wall time, including crowded cave/palace samples."""
import json
from test_runtime import ROOT
from profile_pacing import measure

report = measure(ROOT/'out/release/rom.bin', ROOT/'out/release/symbol.txt')
minimum_presentations={'level1_entry':590,'level2_entry':590,'level3_entry':575,'level4_entry':495,'level5_entry':580,'level6_entry':530,'level7_entry':435,'level8_entry':510,'cave_middle':540,'windows_middle':550,'palace_upper':580,'palace_lower':570}
for case in report['cases']:
    assert case['vblank_overruns']==0,(case['scene'],'late transfer crossed the display deadline')
    if case['scene'] in minimum_presentations:
        assert case['presentation_histogram'].get(1,0)>=minimum_presentations[case['scene']],(case['scene'],'presentation cadence regression')
    if case['scene'] in ('cave_middle','palace_upper','palace_lower'):
        assert case['longest_presentation_gap']<=2,(case['scene'],'longer repeated-frame gap')
        assert case['worst_second_presentations']>=40,case['scene']
    # The sky patrol enters a rescue mode; compare uninterrupted encounters.
    if case['scene'] != 'sky_middle':
        assert case['play_video_frames'] == 600, (case['scene'], 'fixture left PLAY')
        assert abs(case['logic_updates']-600) <= 2, case['scene']
        assert abs(case['timer_steps']-600) <= 3, case['scene']
        # A sampling window can end with a three-tick batch still in flight.
        assert case['worst_second_updates'] >= 57, case['scene']
        assert case['discarded_ticks'] == 0, case['scene']
assert sum(c['catchup_ticks'] for c in report['cases']) > 0
report['passed'] = True
report['criterion'] = 'Uninterrupted 600-refresh PLAY samples: <=2 ticks drift, >=57 ticks in every 60-refresh window, zero discarded ticks. Scene-specific presentation floors guard the v16 cave/palace scheduling gains, with at most two-refresh presentation gaps in the cave/palace patrols, with zero late-VBlank overruns. Does not require 60 distinct rendered frames per second.'
(ROOT/'reports/frame-pacing.json').write_text(json.dumps(report, indent=2)+'\n')

# A short average can hide a later three-refresh hitch in a sustained crowd.
extended=measure(ROOT/'out/release/rom.bin', ROOT/'out/release/symbol.txt', 3600,
                 ('cave_middle','palace_upper','palace_lower'))
long_floors={'cave_middle':3300,'palace_upper':3500,'palace_lower':3540}
for case in extended['cases']:
    assert case['play_video_frames']==3600,case['scene']
    assert abs(case['logic_updates']-3600)<=2,case['scene']
    assert abs(case['timer_steps']-3600)<=3,case['scene']
    assert case['worst_second_updates']>=57,case['scene']
    assert case['discarded_ticks']==case['vblank_overruns']==0,case['scene']
    assert case['longest_presentation_gap']<=2,case['scene']
    assert case['presentation_histogram'].get(1,0)>=long_floors[case['scene']],case['scene']
    assert case['observed_image_changes']>=long_floors[case['scene']]-2,(case['scene'],'counter increased without screen changes')
extended['passed']=True
extended['criterion']='One-minute cave/palace patrols: full simulation speed, no discarded ticks, no late VBlank overruns, no presentation interval beyond two refreshes, at least 3300/3500/3540 cave/upper/lower-palace presentations, corroborated by changes in captured playfield pixels.'
(ROOT/'reports/frame-pacing-extended.json').write_text(json.dumps(extended,indent=2)+'\n')
