from __future__ import annotations
import csv, io, math
from collections import Counter, defaultdict
from datetime import datetime
from ..config import START_MONTH
from ..db import connect

def boolean(value): return str(value).strip().lower() in {"true","1","yes"}
def _rows(content): return list(csv.DictReader(io.StringIO(content.decode() if isinstance(content,bytes) else content)))
def ingest_project(repo, category_dir, files, source, pass_id, as_of, report=None):
    adoption=_rows(files.get("adoption_dates.csv", "")); main=_rows(files.get("commit_stats_main.csv", "")); stats=_rows(files.get("commit_stats_files.csv", "")); report=report or {}
    tool_use, commit_use = boolean(report.get("tool_use")), boolean(report.get("commit_use"))
    with connect("p2") as con:
        for table in ("p2_tool_adoption","p2_commit_month","p2_commit_size","p2_repo"): con.execute(f"DELETE FROM {table} WHERE repo=?",(repo,))
        adoption_date=min((x.get("adoption") for x in adoption if x.get("adoption")), default=None)
        con.execute("INSERT INTO p2_repo VALUES(?,?,?,?,?,?,?,?,?,?,?)",(repo,source,pass_id,as_of,category_dir,int(tool_use),int(commit_use),int(boolean(report.get("ignored_tools"))),adoption_date,report.get("error"),int("dotfiles" in repo.rsplit("/",1)[-1].lower())))
        con.executemany("INSERT OR REPLACE INTO p2_tool_adoption VALUES(?,?,?)",[(repo,x.get("tool"),x.get("adoption")) for x in adoption if x.get("tool") and x.get("adoption")])
        types={x.get("sha"): ("AI" if x.get("auth_type") in {"AI","AI-FOLLOWUP"} else x.get("auth_type"),x.get("tool", "")) for x in main if boolean(x.get("in_main_branch")) and x.get("date","")[:7] >= START_MONTH}
        months=Counter((x.get("date", "")[:7], *types[x["sha"]]) for x in main if x.get("sha") in types)
        for (month, typ, tool), count in months.items():
            con.execute("INSERT OR REPLACE INTO p2_commit_month VALUES(?,?,?,?,?)",(repo,month,typ,tool,count))
        if tool_use and commit_use:
            per=defaultdict(lambda:[0,0,0])
            for x in stats:
                sha=x.get("commit_sha")
                if sha in types: per[sha][0]+=int(x.get("added_lines") or 0); per[sha][1]+=int(x.get("deleted_lines") or 0); per[sha][2]+=1
            hist=Counter()
            for sha,(added,deleted,count) in per.items():
                typ,_=types[sha]; year=next((x.get("date","")[:4] for x in main if x.get("sha")==sha),"")
                for metric,value in (("added",added),("deleted",deleted),("files",count)):
                    hist[(year,typ,metric,value if value<=1000 else 1000+math.floor(math.log2(value)))] += 1
            con.executemany("INSERT OR REPLACE INTO p2_commit_size VALUES(?,?,?,?,?,?)",[(repo,*key,n) for key,n in hist.items()])
        con.commit()
