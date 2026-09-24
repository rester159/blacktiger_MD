#!/usr/bin/env python3
"""Export per-second/rolling presentation comparisons as JSON, CSV and HTML."""
import argparse,csv,json
from pathlib import Path
from cadence_stats import cadence_stats
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True)
p.add_argument('--output',type=Path,required=True,help='Output prefix, without extension')
p.add_argument('--floor',type=int,choices=(15,20,30,40,50,60),default=40)
a=p.parse_args();before=json.loads(a.before.read_text());after=json.loads(a.after.read_text())
assert len(before['cases'])==len(after['cases'])
cases=[]
for b,c in zip(before['cases'],after['cases']):
    assert b['name']==c['name'] and b['refreshes']==c['refreshes']
    x=cadence_stats(b['trace']);y=cadence_stats(c['trace'])
    common=[(u,v) for u,v in zip(x['seconds'],y['seconds']) if u['fps'] is not None and v['fps'] is not None]
    cases.append(dict(name=b['name'],level=b['level']+1,before=x,after=y,
        common_complete_seconds=len(common),
        common_seconds_below_floor_before=sum(u['fps']<a.floor for u,v in common),
        common_seconds_below_floor_after=sum(v['fps']<a.floor for u,v in common),
        common_seconds_below_30_before=sum(u['fps']<30 for u,v in common),
        common_seconds_below_30_after=sum(v['fps']<30 for u,v in common),
        discarded_ticks_before=b['pacing_discarded_ticks'],discarded_ticks_after=c['pacing_discarded_ticks']))
report=dict(target_floor=a.floor,before_rom_sha256=before['rom_sha256'],after_rom_sha256=after['rom_sha256'],
    units='One second = 60 emulated NTSC refreshes; presentations, not distinct images or host display delivery.',
    scope='Same injected starting encounters and controller schedules. Game states can diverge after missed ticks. Partial or interrupted PLAY seconds are null, not extrapolated. Rolling windows overlap and are not independent seconds.',cases=cases)
a.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
with a.output.with_suffix('.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['scene','second','fps_before','fps_after','logic_steps_before','logic_steps_after','discarded_ticks_before','discarded_ticks_after','play_refreshes_before','play_refreshes_after'])
    for c in cases:
        for b,n in zip(c['before']['seconds'],c['after']['seconds']):
            w.writerow([c['name'],b['second'],b['fps'],n['fps'],b['logic_steps'],n['logic_steps'],b['discarded_ticks'],n['discarded_ticks'],b['play_refreshes'],n['play_refreshes']])
html=r'''<!doctype html><meta charset="utf-8"><title>Black Tiger: second-by-second cadence</title>
<style>body{background:#111722;color:#e5eaf3;font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 20px}h1{font-size:27px}p{line-height:1.5}select,button{font:inherit;padding:8px;background:#253146;color:white;border:1px solid #61728c}svg{width:100%;background:#172131;margin-top:20px}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}td,th{padding:7px;text-align:right;border-bottom:1px solid #344057}td:first-child,th:first-child{text-align:left}.low{color:#ffb18b}.legend{color:#65dbbb}.baseline{color:#a8b9ff}.scroll{max-height:500px;overflow:auto}th{position:sticky;top:0;background:#172131}#summary{white-space:pre-line}small{color:#b8c3d5}</style>
<h1>Black Tiger: second-by-second cadence</h1>
<p>Every point counts actual graphics submissions over 60 emulated refreshes. The dashed line is FLOOR FPS. No scene averages. Interrupted PLAY windows are gaps.</p>
<select id="scene"></select> <select id="mode"><option value="seconds">Each second</option><option value="rolling_fps">Rolling one-second windows</option></select>
<p><span class="baseline">■ Before</span> &nbsp; <span class="legend">■ After</span></p>
<div id="summary"></div><svg id="plot" viewBox="0 0 1060 340" role="img" aria-label="Before and after FPS over time"></svg>
<p><small>Hover over a point for its one-second presentation count. Below-FLOOR totals use complete seconds only. Rolling windows expose dips straddling second boundaries.</small></p>
<div class="scroll"><table><thead><tr><th>Second</th><th>FPS before</th><th>FPS after</th><th>Logic before</th><th>Logic after</th><th>Lost ticks before</th><th>Lost ticks after</th></tr></thead><tbody id="rows"></tbody></table></div>
<p><small id="scope"></small></p>
<script>const data=PAYLOAD;
const scene=document.getElementById('scene'),mode=document.getElementById('mode');
for(const [i,c] of data.cases.entries())scene.add(new Option('Level '+c.level+' — '+c.name,i));
const cave=data.cases.findIndex(c=>c.level===4);scene.value=Math.max(cave,0);
const value=v=>v==null?'—':v;
function draw(){const c=data.cases[+scene.value],b=c.before,a=c.after;
document.getElementById('summary').textContent='Worst rolling second: '+b.worst_rolling_second+' → '+a.worst_rolling_second+' FPS\nSeconds below '+data.target_floor+' FPS (same '+c.common_complete_seconds+' complete seconds): '+c.common_seconds_below_floor_before+' → '+c.common_seconds_below_floor_after+'\nLongest consecutive seconds below '+data.target_floor+': '+b.longest_consecutive_seconds_below[data.target_floor]+' → '+a.longest_consecutive_seconds_below[data.target_floor]+'\nLost simulation ticks: '+c.discarded_ticks_before+' → '+c.discarded_ticks_after;
const rolling=mode.value==='rolling_fps',count=b.seconds.length,x=t=>50+t/count*980,y=v=>290-v/60*260;
let svg='';for(let v=0;v<=60;v+=10){svg+='<line x1="50" y1="'+y(v)+'" x2="1030" y2="'+y(v)+'" stroke="'+(v===data.target_floor?'#ffb18b':'#344057')+'" stroke-dasharray="4 5"/><text x="14" y="'+(y(v)+5)+'" fill="#cad3e4">'+v+'</text>';}
for(let t=0;t<=count;t+=5)svg+='<text x="'+x(t)+'" y="320" fill="#cad3e4" text-anchor="middle">'+t+'s</text>';
for(const [stats,color,label] of [[b,'#a8b9ff','Before'],[a,'#65dbbb','After']]){let path='',points='';let active=false;const values=rolling?stats.rolling_fps:stats.seconds.map(s=>s.fps);
values.forEach((v,i)=>{if(v==null){active=false;return;}const t=rolling?(i+60)/60:i+1;path+=(active?'L':'M')+x(t)+','+y(v)+' ';active=true;points+='<circle cx="'+x(t)+'" cy="'+y(v)+'" r="'+(rolling?1:3)+'" fill="'+color+'"><title>'+label+': '+t.toFixed(2)+'s, '+v+' FPS</title></circle>';});svg+='<path d="'+path+'" fill="none" stroke="'+color+'" stroke-width="2"/>'+points;}
document.getElementById('plot').innerHTML=svg;
document.getElementById('rows').innerHTML=b.seconds.map((s,i)=>{const n=a.seconds[i];return '<tr>'+[s.second,s.fps,n.fps,s.logic_steps,n.logic_steps,s.discarded_ticks,n.discarded_ticks].map((v,j)=>'<td class="'+((j===1||j===2)&&v!=null&&v<data.target_floor?'low':'')+'">'+value(v)+'</td>').join('')+'</tr>';}).join('');
document.getElementById('scope').textContent=data.units+' '+data.scope;}
scene.onchange=mode.onchange=draw;draw();</script>'''
a.output.with_suffix('.html').write_text(html.replace('FLOOR',str(a.floor)).replace('PAYLOAD',json.dumps(report,separators=(',',':'))))
print(f'Wrote {a.output}.json, .csv and .html')
