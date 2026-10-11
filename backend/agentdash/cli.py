from __future__ import annotations

import argparse
from datetime import datetime, timezone

from .db import acquire_lock, connect, init_schema, release_lock


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sync(args: argparse.Namespace) -> None:
    acquired = not args.lock_held
    if acquired and not acquire_lock(args.source):
        raise RuntimeError(f"Đang có job {args.source} chạy")
    with connect("jobs") as database:
        job_id = database.execute(
            "INSERT INTO job(source,started_at,status) VALUES(?,?,?)",
            (args.source, _now(), "running"),
        ).lastrowid
    try:
        if args.source == "p2":
            from .config import github_tokens
            from .sources.p2_live import run_live
            run_live(github_tokens(), args.chunks, args.limit)
        else:
            from .config import github_tokens
            from .github import GitHubClient
            with GitHubClient(github_tokens()) as client:
                if args.source == "global":
                    from .sources.global_search import sync_global
                    sync_global(client)
                else:
                    from .sources.p3_panel import sync_panel
                    sync_panel(client, args.max_minutes, args.limit)
                    if args.enrich:
                        from .sources.p3_enrich import enrich
                        enrich(client)
        from .export import export
        export(args.out)
    except Exception as error:
        with connect("jobs") as database:
            database.execute("UPDATE job SET finished_at=?,status=?,message=? WHERE id=?", (_now(), "failed", str(error), job_id))
        raise
    else:
        with connect("jobs") as database:
            database.execute("UPDATE job SET finished_at=?,status=? WHERE id=?", (_now(), "done", job_id))
    finally:
        release_lock(args.source)


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentdash")
    sub = parser.add_subparsers(dest="command", required=True)
    baseline = sub.add_parser("baseline"); baseline.add_argument("source", choices=["p3"])
    ingest = sub.add_parser("ingest"); ingest.add_argument("source", choices=["zenodo"]); ingest.add_argument("--keep", action="store_true")
    sync = sub.add_parser("sync")
    sync.add_argument("source", choices=["global", "p2", "p3"])
    sync.add_argument("--enrich", action="store_true")
    sync.add_argument("--max-minutes", type=int, default=50)
    sync.add_argument("--chunks", type=int)
    sync.add_argument("--limit", type=int)
    sync.add_argument("--out")
    sync.add_argument("--lock-held", action="store_true", help=argparse.SUPPRESS)
    export = sub.add_parser("export"); export.add_argument("--out")
    state = sub.add_parser("state"); state.add_argument("action", choices=["pull", "push"]); state.add_argument("--sources", required=True)
    serve = sub.add_parser("serve"); serve.add_argument("--host", default="127.0.0.1"); serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    init_schema()
    if args.command == "baseline":
        from .sources.p3_baseline import reproduce_baseline
        reproduce_baseline()
    elif args.command == "ingest":
        from .sources.p2_zenodo import ingest_zenodo
        ingest_zenodo(args.keep)
    elif args.command == "sync":
        _sync(args)
    elif args.command == "export":
        from .export import export
        export(args.out)
    elif args.command == "state":
        from . import state as release_state
        getattr(release_state, args.action)(args.sources)
    elif args.command == "serve":
        import uvicorn
        uvicorn.run("agentdash.api:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
