from __future__ import annotations
import hashlib
import lizard
from ..config import P3_HUMAN_ENRICH_PCT
from ..db import connect

EXTENSIONS={".py",".js",".ts",".swift",".rs",".go",".cpp",".c",".h",".cs",".java",".tsx"}
EXCLUDED=("lock","json","yaml","yml","routes.js","routes.d.ts","conftest.py","index.tsx",".lockb")
def average_complexity(files):
    values=[]
    for file in files:
        path=file.get("filename",""); patch=file.get("patch","") or ""
        if len(patch)>10000 or not path.endswith(tuple(EXTENSIONS)) or any(x in path.lower() for x in EXCLUDED) or "/.claude/" in path or "/.hive-mind/" in path: continue
        code="\n".join(line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
        analysis=lizard.analyze_file.analyze_source_code(path, code); functions=analysis.function_list
        values.append(sum(f.cyclomatic_complexity for f in functions)/len(functions) if functions else 1.0)
    return sum(values)/len(values) if values else None

def enrich(client):
    with connect("p3") as con:
        rows=con.execute("SELECT node_id,repo,number,class FROM p3_pr WHERE enriched_at IS NULL").fetchall()
        for node_id,repo,number,kind in rows:
            selected=kind in {"Copilot","Devin","Jules","Codex","Cursor","Claude Code"} or (kind=="Human" and int(hashlib.sha1(node_id.encode()).hexdigest(),16)%100<P3_HUMAN_ENRICH_PCT)
            if not selected: con.execute("UPDATE p3_pr SET enrich_selected=0 WHERE node_id=?",(node_id,)); continue
            owner,name=repo.split("/",1); files=list(client.rest_paged(f"/repos/{owner}/{name}/pulls/{number}" + "/files"))[:3000]
            bot=human=0
            data=client.graphql("query($id:ID!){node(id:$id){... on PullRequest{comments(first:100){nodes{author{__typename}}} reviews(first:100){nodes{author{__typename}}}}}}",{"id":node_id})["node"]
            for group in (data["comments"]["nodes"],data["reviews"]["nodes"]):
                for x in group:
                    if (x.get("author") or {}).get("__typename")=="Bot": bot+=1
                    else: human+=1
            con.execute("UPDATE p3_pr SET enrich_selected=1,enriched_at=datetime('now'),files_changed=?,hunks=?,diff_size=?,churn=?,avg_cc=?,comments_bot=?,comments_human=? WHERE node_id=?",(len(files),sum((x.get("patch") or "").count("@@ -") for x in files),sum(max(x.get("additions",0),x.get("deletions",0)) for x in files),sum(x.get("additions",0)+x.get("deletions",0) for x in files),average_complexity(files),bot,human,node_id))
        con.commit()
