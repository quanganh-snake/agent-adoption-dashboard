from __future__ import annotations
from datetime import datetime, timedelta, timezone
from ..config import OPENAI_API_KEY, START_MONTH
from ..db import connect
from .p3_classify import classify_pr
from .taskclass import classify_task

QUERY = '''query($owner:String!,$name:String!,$cursor:String){repository(owner:$owner,name:$name){pullRequests(first:100,after:$cursor,orderBy:{field:CREATED_AT,direction:DESC}){pageInfo{endCursor hasNextPage}nodes{id number title bodyText createdAt mergedAt closedAt state headRefName author{__typename login}}}}}'''
INCREMENTAL_QUERY = '''query($owner:String!,$name:String!,$cursor:String){repository(owner:$owner,name:$name){pullRequests(first:100,after:$cursor,orderBy:{field:UPDATED_AT,direction:DESC}){pageInfo{endCursor hasNextPage}nodes{id number title bodyText createdAt updatedAt mergedAt closedAt state headRefName author{__typename login}}}}}'''

def _save_pr(con, repo: str, node: dict, human_baseline: bool):
    author = node.get("author") or {}; kind = classify_pr(author.get("login"), author.get("__typename"), node.get("headRefName"), node.get("bodyText"))
    task, source = classify_task(node.get("title", ""), node.get("bodyText"), OPENAI_API_KEY) if kind in {"Copilot","Devin","Jules","Codex","Cursor","Claude Code"} or (kind == "Human" and human_baseline) else (None, None)
    con.execute('''INSERT INTO p3_pr(node_id,repo,number,created_at,merged_at,closed_at,state,author_login,author_type,head_ref,title,class,task_type,task_source)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(node_id) DO UPDATE SET merged_at=excluded.merged_at,closed_at=excluded.closed_at,state=excluded.state,title=excluded.title,class=excluded.class,task_type=excluded.task_type,task_source=excluded.task_source''', (node["id"],repo,node["number"],node["createdAt"],node.get("mergedAt"),node.get("closedAt"),node["state"],author.get("login"),author.get("__typename"),node.get("headRefName"),node.get("title"),kind,task,source))

def sync_panel(client, max_minutes: int = 50, limit: int | None = None):
    deadline = datetime.now(timezone.utc) + timedelta(minutes=max_minutes)
    cutoff = f"{START_MONTH}-01"
    with connect("p3") as con:
        repos = con.execute(
            "SELECT repo,human_baseline,backfill_cursor FROM p3_repo "
            "WHERE backfill_done=0 ORDER BY repo"
        ).fetchall()
        if limit is not None:
            repos = repos[:limit]
        for repo, baseline, cursor in repos:
            if datetime.now(timezone.utc) >= deadline:
                break
            owner, name = repo.split("/", 1)
            try:
                data = client.graphql(QUERY, {"owner": owner, "name": name, "cursor": cursor})
            except RuntimeError as exc:
                if "NOT_FOUND" in str(exc):
                    con.execute(
                        "UPDATE p3_repo SET backfill_done=1,stars=-1 WHERE repo=?",
                        (repo,),
                    )
                    con.commit()
                    continue
                raise
            page = data["repository"]["pullRequests"]
            for node in page["nodes"]:
                _save_pr(con, repo, node, bool(baseline))
            old = any(node["createdAt"][:10] < cutoff for node in page["nodes"])
            con.execute(
                "UPDATE p3_repo SET backfill_cursor=?,backfill_done=? WHERE repo=?",
                (
                    page["pageInfo"]["endCursor"],
                    int(old or not page["pageInfo"]["hasNextPage"]),
                    repo,
                ),
            )
            con.commit()
        remaining = None if limit is None else max(0, limit - len(repos))
        completed = con.execute(
            "SELECT repo,human_baseline,last_incremental_at FROM p3_repo "
            "WHERE backfill_done=1 AND stars>=0 ORDER BY COALESCE(last_incremental_at,'')"
        ).fetchall()
        if remaining is not None:
            completed = completed[:remaining]
        for repo, baseline, last_incremental_at in completed:
            if datetime.now(timezone.utc) >= deadline:
                break
            owner, name = repo.split("/", 1)
            data = client.graphql(
                INCREMENTAL_QUERY,
                {"owner": owner, "name": name, "cursor": None},
            )
            nodes = data["repository"]["pullRequests"]["nodes"]
            cutoff = (
                datetime.fromisoformat(last_incremental_at.replace("Z", "+00:00")) - timedelta(days=1)
                if last_incremental_at else None
            )
            for node in nodes:
                updated_at = datetime.fromisoformat(node["updatedAt"].replace("Z", "+00:00"))
                if cutoff and updated_at < cutoff:
                    break
                _save_pr(con, repo, node, bool(baseline))
            con.execute(
                "UPDATE p3_repo SET last_incremental_at=? WHERE repo=?",
                (datetime.now(timezone.utc).isoformat(), repo),
            )
            con.commit()
