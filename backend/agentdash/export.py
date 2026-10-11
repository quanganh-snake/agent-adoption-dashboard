"""Build immutable JSON snapshots consumed by the frontend."""
from __future__ import annotations

import json
from contextlib import ExitStack
from datetime import date, datetime, timezone
from pathlib import Path

from .metrics import global_, p2, p3


def _cfg(key, default):
    from . import config
    return getattr(config, key, default)


def _months(start, end):
    year, month = map(int, start.split("-")); result = []
    while (year, month) <= (end.year, end.month):
        result.append(f"{year}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return result


def _dump(out, name, value):
    (out / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _one(database, query, args=()):
    row = database.execute(query, args).fetchone()
    return row[0] if row else None


def _row(identifier, group, label, unit, months, values, counts=None, provisional=(), low_n=(), source_ids=()):
    return {"id": identifier, "group": group, "label_vi": label, "unit": unit,
            "values": dict(zip(months, values)), "n": dict(zip(months, counts or [None] * len(months))),
            "provisional": list(provisional), "low_n": list(low_n), "source_ids": list(source_ids)}


def _comparison(label, paper=None, reproduced=None, latest=None, **fields):
    return {"chỉ_số": label, **fields, "paper": paper or {}, "reproduced": reproduced or {}, "latest": latest or {}}


def _comparisons(p2db, p3db):
    p2_latest = _one(p2db, "SELECT COUNT(*) FROM p2_repo WHERE is_dotfiles=0 AND COALESCE(error,'')='' ")
    p2_adopters = _one(p2db, "SELECT COUNT(*) FROM p2_repo WHERE is_dotfiles=0 AND COALESCE(error,'')='' AND adoption_date IS NOT NULL")
    adoption = round(100 * p2_adopters / p2_latest, 4) if p2_latest else None
    tool_rows = [dict(row) for row in p2db.execute("SELECT tool, COUNT(*) n FROM p2_tool_adoption GROUP BY tool ORDER BY tool")]
    latest_p3 = p3.yearly(p3db, [2026], date.today())
    agent = latest_p3["per_key"]["Agent"]["2026"]
    human = latest_p3["per_key"]["Human"]["2026"]
    per_agent = latest_p3["per_key"]
    task = latest_p3["task_merge_rate_pct"].get("2026", {})
    comments = latest_p3["bot_comment_share_pct"].get("2026", {})
    return {
        "p2_table1": [_comparison("Ước tính tiếp nhận bảo thủ", {"tỷ_lệ_%": 22.2}, latest={"tỷ_lệ_%": adoption}), _comparison("Ước tính tiếp nhận cao", {"tỷ_lệ_%": 28.66}, latest={"tỷ_lệ_%": adoption})],
        "p2_tools": [_comparison(row["tool"], {"repos": {"Copilot": 13890, "Claude Code": 12053, "Cursor": 2965, "Codex": 2147, "Gemini": 1256, "CodeRabbit": 1249}.get(row["tool"])}, latest={"repos": row["n"]}) for row in tool_rows],
        "p3_table2": [_comparison("Agent", {"merge_rate_pct": 71.5, "ttm_mean_h": 19.43}, latest={"merge_rate_pct": agent["merge_rate_pct"], "ttm_mean_h": agent["ttm_mean_h"]}), _comparison("Human", {"merge_rate_pct": 77.2, "ttm_mean_h": 63.89}, latest={"merge_rate_pct": human["merge_rate_pct"], "ttm_mean_h": human["ttm_mean_h"]})],
        "p3_table3": [],
        "p3_table4": [_comparison(name, latest={"merge_rate_pct": values["2026"]["merge_rate_pct"], "prs": values["2026"]["prs"]}) for name, values in per_agent.items() if name not in {"Agent", "Human"}],
        "p3_table5": [_comparison(name, {"agent_merge_rate_pct": {"Docs & Style": 83.8, "Feature & Behavior": 68.7, "Infrastructure": 72.9, "Internal Quality": 74.3}.get(name)}, latest={"agent_merge_rate_pct": values["Agent"], "human_merge_rate_pct": values["Human"]}) for name, values in task.items()],
        "p3_table6_paper_only": [],
        "p3_table7": [_comparison(name, latest={"bot_comment_share_pct": value}) for name, value in comments.items()],
    }


def export(out: str | Path | None = None):
    from .baseline import REFERENCES, VALUES
    from .config import DATA_DIR
    from .db import connect, init_schema
    init_schema()
    output = Path(out) if out else DATA_DIR / "snapshots"; output.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        p2db, p3db, gdb = (stack.enter_context(connect(name)) for name in ("p2", "p3", "global"))
        latest = [date.fromisoformat(str(value)[:10]) for value in (_one(p2db, "SELECT MAX(as_of) FROM p2_repo"), _one(p3db, "SELECT MAX(created_at) FROM p3_pr"), _one(gdb, "SELECT MAX(fetched_at) FROM gs_count")) if value]
        ytd = min(latest) if latest else date.today(); months = _months(_cfg("START_MONTH", "2024-01"), ytd); years = [2024, 2025, 2026]
        ps, p3s, gs = p2.series(p2db, months, ytd), p3.series(p3db, months, ytd), global_.series(gdb, months)
        pass_id = _one(p2db, "SELECT MAX(pass_id) FROM p2_pass")
        total = _one(p2db, "SELECT total FROM p2_pass WHERE pass_id=?", (pass_id,)) if pass_id else None
        completed = _one(p2db, "SELECT COALESCE(SUM(n_repos),0) FROM p2_chunk WHERE pass_id=? AND status='done'", (pass_id,)) if pass_id else None
        progress = round(100 * completed / total, 4) if total else None
        def checks(database, table):
            return [dict(row) | {"deviation_flag": abs((row["reproduced"] or 0) - (row["paper"] or 0)) > .1} for row in database.execute(f"SELECT metric,paper,reproduced FROM {table}")]
        meta = {"generated_at": datetime.now(timezone.utc).isoformat(), "ytd_until": ytd.isoformat(), "agent_impact_commit": _cfg("AGENT_IMPACT_COMMIT", ""), "sources": {"p2": {"as_of_min": _one(p2db, "SELECT MIN(as_of) FROM p2_repo"), "as_of_max": _one(p2db, "SELECT MAX(as_of) FROM p2_repo"), "repos_total": _one(p2db, "SELECT COUNT(*) FROM p2_repo"), "repos_live": _one(p2db, "SELECT COUNT(*) FROM p2_repo WHERE source='live'"), "pass_id": pass_id, "pass_progress_pct": progress, "seed": "zenodo-19256968"}, "p3": {"as_of": _one(p3db, "SELECT MAX(created_at) FROM p3_pr"), "repos": _one(p3db, "SELECT COUNT(*) FROM p3_repo"), "prs_total": _one(p3db, "SELECT COUNT(*) FROM p3_pr"), "enriched_total": _one(p3db, "SELECT COUNT(*) FROM p3_pr WHERE enriched_at IS NOT NULL")}, "global": {"as_of": _one(gdb, "SELECT MAX(fetched_at) FROM gs_count"), "cells": _one(gdb, "SELECT COUNT(*) FROM gs_count")}}, "warnings": []}
        month_2026 = [month for month in months if month.startswith("2026-")]
        indexes = [months.index(month) for month in month_2026]
        p3_n = p3s["prs"]["Agent"]
        rows = [_row("p2-adoption", "p2", "Tỷ lệ tiếp nhận tích lũy", "%", month_2026, [ps["adoption_rate_pct"][i] for i in indexes], [ps["denominator"][i] for i in indexes], source_ids=["P2-06"]), _row("p2-ai-share", "p2", "Tỷ trọng commit AI", "%", month_2026, [ps["ai_commit_share_pct"][i] for i in indexes], source_ids=["P2-06"]), _row("p3-agent-merge", "p3", "Tỷ lệ merge Agent", "%", month_2026, [p3s["merge_rate_pct"]["Agent"][i] for i in indexes], [p3_n[i] for i in indexes], [month_2026[n] for n, i in enumerate(indexes) if p3s["provisional"][i]], [month_2026[n] for n, i in enumerate(indexes) if (p3_n[i] or 0) < 30], ["P3-06"]), _row("global-agent-share", "global", "Tỷ trọng PR agent", "%", month_2026, [gs["agent_share_pct"][i] for i in indexes], source_ids=["P2-06"])]
        _dump(output, "meta", meta); _dump(output, "baseline", {"references": REFERENCES, "values": [value.__dict__ for value in VALUES], "checks": {"p2": checks(p2db, "p2_check"), "p3": checks(p3db, "p3_baseline_check")}}); _dump(output, "series", {"months": months, "p2": ps, "p3": p3s, "global": gs}); _dump(output, "yearly", {"years": years, "ytd_until": ytd.isoformat(), "p2": p2.yearly(p2db, years, ytd), "p3": p3.yearly(p3db, years, ytd), "global": global_.yearly(gdb, years)}); _dump(output, "monthly_2026", {"months": month_2026, "rows": rows}); _dump(output, "paper_vs_latest", _comparisons(p2db, p3db))
    return output
