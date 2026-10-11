from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import DATA_DIR

SCHEMAS = {
"global": "CREATE TABLE IF NOT EXISTS gs_count(query_id TEXT,month TEXT,metric TEXT CHECK(metric IN('created','merged')),count INTEGER,fetched_at TEXT,PRIMARY KEY(query_id,month,metric));",
"p3": '''CREATE TABLE IF NOT EXISTS p3_repo(repo TEXT PRIMARY KEY,stars INTEGER,human_baseline INTEGER,backfill_done INTEGER DEFAULT 0,backfill_cursor TEXT,last_incremental_at TEXT);
CREATE TABLE IF NOT EXISTS p3_pr(node_id TEXT PRIMARY KEY,repo TEXT,number INTEGER,created_at TEXT,merged_at TEXT,closed_at TEXT,state TEXT,author_login TEXT,author_type TEXT,head_ref TEXT,title TEXT,class TEXT,task_type TEXT,task_source TEXT,enrich_selected INTEGER,enriched_at TEXT,files_changed INTEGER,hunks INTEGER,diff_size INTEGER,churn INTEGER,avg_cc REAL,comments_bot INTEGER,comments_human INTEGER);
CREATE TABLE IF NOT EXISTS p3_baseline_check(metric TEXT PRIMARY KEY,paper REAL,reproduced REAL);''',
"p2": '''CREATE TABLE IF NOT EXISTS p2_repo(repo TEXT PRIMARY KEY,source TEXT CHECK(source IN('zenodo','live')),pass_id INTEGER,as_of TEXT,category TEXT,tool_use INTEGER,commit_use INTEGER,ignored_tools INTEGER,adoption_date TEXT,error TEXT,is_dotfiles INTEGER);
CREATE TABLE IF NOT EXISTS p2_tool_adoption(repo,tool,adoption_date,PRIMARY KEY(repo,tool));
CREATE TABLE IF NOT EXISTS p2_commit_month(repo,month,auth_type,tool,n,PRIMARY KEY(repo,month,auth_type,tool));
CREATE TABLE IF NOT EXISTS p2_commit_size(repo,year,auth_type,metric,bin,n,PRIMARY KEY(repo,year,auth_type,metric,bin));
CREATE TABLE IF NOT EXISTS p2_pass(pass_id INTEGER PRIMARY KEY,seed INTEGER,started_at,finished_at,total);
CREATE TABLE IF NOT EXISTS p2_chunk(pass_id,chunk_idx,status,started_at,finished_at,n_repos,n_errors,PRIMARY KEY(pass_id,chunk_idx));
CREATE TABLE IF NOT EXISTS p2_check(metric TEXT PRIMARY KEY,paper REAL,reproduced REAL);''',
"jobs": "CREATE TABLE IF NOT EXISTS job(id INTEGER PRIMARY KEY,source,started_at,finished_at,status,message);",
}


def db_path(name: str) -> Path:
    return DATA_DIR / "state" / f"{name}.db"

@contextmanager
def connect(name: str):
    path = db_path(name); path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    try:
        yield con
        con.commit()
    finally:
        con.close()

def lock_path(source: str) -> Path:
    return DATA_DIR / "state" / f"{source}.lock"

def acquire_lock(source: str) -> bool:
    path = lock_path(source); path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.touch(exist_ok=False)
    except FileExistsError:
        return False
    return True

def release_lock(source: str) -> None:
    lock_path(source).unlink(missing_ok=True)

def init_schema() -> None:
    for name, schema in SCHEMAS.items():
        with connect(name) as con:
            con.executescript(schema); con.commit()
