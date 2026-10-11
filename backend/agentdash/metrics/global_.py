"""GitHub Search API metric transformations."""
from collections import defaultdict
QUERIES=('all','copilot','codex','devin','cursor','claude_code','jules')
def series(db,months):
 rows=[dict(r) for r in db.execute('SELECT query_id,month,metric,count FROM gs_count').fetchall()]; index={(r['query_id'],r['month'],r['metric']):r['count'] for r in rows}; out={'created':{},'merged':{}}
 for metric in ('created','merged'):
  out[metric]={q:[index.get((q,m,metric)) for m in months] for q in QUERIES}
 out['agent_share_pct']=[round(100*sum(index.get((q,m,'created'),0) for q in QUERIES[1:])/index[('all',m,'created')],4) if index.get(('all',m,'created')) else None for m in months]
 return out
def yearly(db,years):
 rows=[dict(r) for r in db.execute('SELECT query_id,month,metric,count FROM gs_count').fetchall()]; result={'created':{},'merged':{},'agent_share_pct':{}}
 for metric in ('created','merged'):
  result[metric]={q:{str(y):sum(r['count'] for r in rows if r['query_id']==q and r['metric']==metric and r['month'].startswith(str(y))) for y in years} for q in QUERIES}
 for y in years:
  all_=result['created']['all'][str(y)]; result['agent_share_pct'][str(y)]=round(100*sum(result['created'][q][str(y)] for q in QUERIES[1:])/all_,4) if all_ else None
 return result
