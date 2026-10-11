from __future__ import annotations
import csv, os, random, shutil, subprocess
from datetime import datetime, timezone
from ..config import DATA_DIR, P2_CHUNK_SIZE, P2_WORKERS, ROOT
from ..db import connect
from .p2_zenodo import ingest_output_tree

def start_pass():
    rows=list(csv.DictReader((ROOT/"vendor/agent-impact/data/projects-29-08.csv").open()))
    with connect("p2") as con:
        pass_id=con.execute("SELECT COALESCE(MAX(pass_id),0)+1 FROM p2_pass").fetchone()[0]
        random.Random(pass_id).shuffle(rows)
        con.execute("INSERT INTO p2_pass VALUES(?,?,?,?,?)",(pass_id,pass_id,datetime.now(timezone.utc).isoformat(),None,len(rows)))
        con.executemany("INSERT INTO p2_chunk VALUES(?,?,'pending',NULL,NULL,?,NULL)",[(pass_id,i,len(rows[i*P2_CHUNK_SIZE:(i+1)*P2_CHUNK_SIZE])) for i in range((len(rows)+P2_CHUNK_SIZE-1)//P2_CHUNK_SIZE)])
        con.commit()
    return pass_id,rows

def run_live(tokens, chunks=None, limit=None):
    pass_id,rows=start_pass(); count=(len(rows)+P2_CHUNK_SIZE-1)//P2_CHUNK_SIZE
    targets=range(min(chunks,count)) if chunks is not None else range(count)
    for idx in targets:
        if shutil.disk_usage(DATA_DIR).free < 20*1024**3: raise RuntimeError("Không đủ dung lượng đĩa (<20GiB)")
        subset=rows[idx*P2_CHUNK_SIZE:(idx+1)*P2_CHUNK_SIZE]
        if limit is not None: subset=subset[:limit]
        work=DATA_DIR/f"work/p2/pass{pass_id}_chunk{idx}.csv"; work.parent.mkdir(parents=True,exist_ok=True)
        with work.open("w",newline="") as output:
            writer=csv.DictWriter(output,fieldnames=["project_name","github_url"])
            writer.writeheader()
            writer.writerows({key: row.get(key, "") for key in writer.fieldnames} for row in subset)
        out=DATA_DIR/"work/p2/out"
        command=["uv","run","--project",".","python","run.py",str(work.resolve()),f"pass{pass_id}_chunk{idx}","--analyze-all","--analysis-date","2024-01-01","--max-workers",str(P2_WORKERS),"--output-dir",str(out.resolve())]
        result=subprocess.run(command,cwd=ROOT/"vendor/agent-impact/code",env={**os.environ,"AIE_GITHUB_TOKENS":",".join(tokens)},capture_output=True,text=True)
        with connect("p2") as con:
            con.execute("UPDATE p2_chunk SET status=?,finished_at=? WHERE pass_id=? AND chunk_idx=?",("done" if result.returncode==0 else "failed",datetime.now(timezone.utc).isoformat(),pass_id,idx)); con.commit()
        if result.returncode: shutil.rmtree(out,ignore_errors=True); continue
        ingest_output_tree(out,"live",pass_id,datetime.now(timezone.utc).isoformat())
        work.unlink(missing_ok=True); shutil.rmtree(out,ignore_errors=True)
