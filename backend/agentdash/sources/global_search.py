from __future__ import annotations
from calendar import monthrange
from datetime import date
from ..config import START_MONTH
from ..db import connect
QUERIES={"all":"is:pr","copilot":"is:pr author:app/copilot-swe-agent","codex":"is:pr head:codex/","devin":"is:pr author:app/devin-ai-integration","cursor":"is:pr head:cursor/","claude_code":'is:pr "Co-Authored-By: Claude" in:body',"jules":"is:pr author:app/google-labs-jules"}
def months():
 y,m=map(int,START_MONTH.split("-")); today=date.today()
 while (y,m)<=(today.year,today.month):
  yield f"{y:04d}-{m:02d}"; y,m=(y+1,1) if m==12 else (y,m+1)
def sync_global(client):
 today=date.today()
 with connect("global") as con:
  for month in months():
   y,m=map(int,month.split("-")); end=monthrange(y,m)[1]
   for query_id,qualifier in QUERIES.items():
    for metric,merged in (("created", ""),("merged"," is:merged")):
     q=f"{qualifier} created:{month}-01..{month}-{end}{merged}"
     try: count=client.search_count(q)
     except Exception: continue
     con.execute("INSERT OR REPLACE INTO gs_count VALUES(?,?,?,?,datetime('now'))",(query_id,month,metric,count))
  con.commit()
