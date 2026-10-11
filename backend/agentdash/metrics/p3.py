"""Metrics for the fixed AIDev repository panel."""
from __future__ import annotations
from collections import defaultdict
from datetime import date, datetime
from statistics import median

from ..sources.taskclass import TASK_CATEGORY_MAP
AGENTS=('Codex','Devin','Copilot','Cursor','Claude Code','Jules')
PAPER_AGENTS=AGENTS[:-1]
def _pct(n,d): return round(100*n/d,4) if d else None
def _rows(db,q,a=()): return [dict(x) for x in db.execute(q,a).fetchall()]
def _aggregate(rows):
    n=len(rows); merged=[r for r in rows if r['merged_at']]
    def parse(value):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    hours=[(parse(r['merged_at'])-parse(r['created_at'])).total_seconds()/3600 for r in merged if r['created_at']]
    return {'prs':n,'merged':len(merged),'merge_rate_pct':_pct(len(merged),n),'ttm_mean_h':round(sum(hours)/len(hours),4) if hours else None,'ttm_median_h':median(hours) if hours else None}
def series(db, months, ytd_until):
    rows=_rows(db,"SELECT p.*, r.human_baseline FROM p3_pr p LEFT JOIN p3_repo r ON r.repo=p.repo")
    keys=(*AGENTS,'Agent','Human'); out={'prs':{k:[] for k in keys},'merge_rate_pct':{k:[] for k in keys},'ttm_mean_h':{k:[] for k in keys},'ttm_median_h':{k:[] for k in keys},'provisional':[]}
    for m in months:
        mr=[r for r in rows if (r['created_at'] or '')[:7]==m]
        for k in keys:
            selected=[r for r in mr if (r['class']==k if k in AGENTS else r['class'] in PAPER_AGENTS if k=='Agent' else r['class']=='Human' and r['human_baseline'])]
            stats=_aggregate(selected)
            for metric in ('prs','merge_rate_pct','ttm_mean_h','ttm_median_h'): out[metric][k].append(stats[metric] if selected else None)
        year,num=map(int,m.split('-')); out['provisional'].append((date(year,num,28) > ytd_until.fromordinal(ytd_until.toordinal()-30)))
    return out
def yearly(db, years, ytd_until):
    rows=_rows(db,"SELECT p.*, r.human_baseline FROM p3_pr p LEFT JOIN p3_repo r ON r.repo=p.repo")
    keys=(*AGENTS,'Agent','Human'); result={'per_key':{k:{} for k in keys},'task_merge_rate_pct':{},'bot_comment_share_pct':{},'median_files':{},'median_hunks':{},'mean_cc':{}}
    for y in years:
      yr=[r for r in rows if (r['created_at'] or '')[:4]==str(y)]
      for k in keys:
       s=[r for r in yr if (r['class']==k if k in AGENTS else r['class'] in PAPER_AGENTS if k=='Agent' else r['class']=='Human' and r['human_baseline'])]; result['per_key'][k][str(y)]=_aggregate(s)
      result['task_merge_rate_pct'][str(y)]={}; result['bot_comment_share_pct'][str(y)]={}; result['median_files'][str(y)]={}; result['median_hunks'][str(y)]={}; result['mean_cc'][str(y)]={}
      for k in ('Agent','Human'):
       s=[r for r in yr if (r['class'] in PAPER_AGENTS if k=='Agent' else r['class']=='Human' and r['human_baseline'])]; result['bot_comment_share_pct'][str(y)][k]=_pct(sum(r['comments_bot'] or 0 for r in s),sum((r['comments_bot'] or 0)+(r['comments_human'] or 0) for r in s)); result['median_files'][str(y)][k]=median([r['files_changed'] for r in s if r['files_changed'] is not None]) if any(r['files_changed'] is not None for r in s) else None; result['median_hunks'][str(y)][k]=median([r['hunks'] for r in s if r['hunks'] is not None]) if any(r['hunks'] is not None for r in s) else None; cc=[r['avg_cc'] for r in s if (r['avg_cc'] or 0)>0]; result['mean_cc'][str(y)][k]=sum(cc)/len(cc) if cc else None
      for task in ('Feature & Behavior','Docs & Style','Infrastructure','Internal Quality'):
       result['task_merge_rate_pct'][str(y)][task]={k:_pct(sum(r['merged_at'] is not None for r in yr if TASK_CATEGORY_MAP.get(r['task_type'])==task and (r['class'] in PAPER_AGENTS if k=='Agent' else r['class']=='Human')),sum(1 for r in yr if TASK_CATEGORY_MAP.get(r['task_type'])==task and (r['class'] in PAPER_AGENTS if k=='Agent' else r['class']=='Human'))) for k in ('Agent','Human')}
    return result
