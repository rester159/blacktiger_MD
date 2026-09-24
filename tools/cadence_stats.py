"""Presentation counts in explicit 60-refresh seconds, without scene averaging."""
def cadence_stats(trace):
    seconds=[]
    for start in range(0,len(trace),60):
        rows=trace[start:start+60]
        full=len(rows)==60 and all(r[0] for r in rows)
        seconds.append(dict(second=start//60+1,start_refresh=start,refreshes=len(rows),
            play_refreshes=sum(r[0] for r in rows),
            fps=sum(r[1] for r in rows) if full else None,
            logic_steps=sum(r[2] for r in rows) if full else None,
            discarded_ticks=sum(r[13] for r in rows) if all(len(r)>13 for r in rows) else None))
    rolling=[]
    shown=playing=0
    for i,row in enumerate(trace):
        shown+=row[1];playing+=row[0]
        if i>=60:shown-=trace[i-60][1];playing-=trace[i-60][0]
        if i>=59:rolling.append(shown if playing==60 else None)
    def longest(values,threshold):
        maximum=run=0
        for value in values:
            run=run+1 if value is not None and value<threshold else 0
            maximum=max(maximum,run)
        return maximum
    valid=[r['fps'] for r in seconds if r['fps'] is not None]
    return dict(seconds=seconds,complete_play_seconds=len(valid),
        seconds_below={str(n):sum(v<n for v in valid) for n in (15,20,30,40,50,60)},
        longest_consecutive_seconds_below={str(n):longest([r['fps'] for r in seconds],n) for n in (15,20,30,40,50,60)},
        longest_consecutive_seconds_below_30=longest([r['fps'] for r in seconds],30),
        worst_rolling_second=min((v for v in rolling if v is not None),default=None),
        rolling_fps=rolling,rolling_start_refresh=0,
        longest_consecutive_rolling_windows_below_30=longest(rolling,30))
