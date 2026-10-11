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
    latest_tools = {row["tool"]: row["n"] for row in p2db.execute("SELECT tool, COUNT(*) n FROM p2_tool_adoption GROUP BY tool")}
    reproduced = {row["metric"]: row["reproduced"] for row in p3db.execute("SELECT metric,reproduced FROM p3_baseline_check")}
    latest_p3 = p3.yearly(p3db, [2026], date.today())
    per_key = latest_p3["per_key"]
    tasks = latest_p3["task_merge_rate_pct"].get("2026", {})
    comments = latest_p3["bot_comment_share_pct"].get("2026", {})
    table4_paper = {
        "Codex": (4297, 2833, 65.9, 32.54), "Devin": (3485, 1811, 52.0, 43.13),
        "Copilot": (3368, 1425, 42.3, 85.40), "Cursor": (918, 567, 61.8, 24.52),
        "Claude Code": (276, 130, 47.1, 42.92),
    }
    table5_paper = {
        "Docs & Style": {"Agent": (4075, 3413, 83.8), "Human": (578, 450, 77.9)},
        "Feature & Behavior": {"Agent": (22896, 15725, 68.7), "Human": (3812, 2952, 77.4)},
        "Infrastructure": {"Agent": (1934, 1410, 72.9), "Human": (1561, 1202, 77.0)},
        "Internal Quality": {"Agent": (4644, 3451, 74.3), "Human": (552, 415, 75.2)},
    }
    liwc = {"Tone": (61.06, 65.62), "Analytic": (56.79, 54.19), "Clout": (39.28, 41.85), "Authentic": (45.68, 44.86), "WC": (49.19, 63.59), "polite": (1.96, 2.13), "insight": (2.68, 2.85), "cause": (2.49, 2.84), "anger": (0.02, 0.02), "anx": (0.01, 0.02), "Social": (8.73, 9.62)}
    tools_paper = {"Copilot": 13890, "Claude Code": 12053, "Cursor": 2965, "Codex": 2147, "Gemini": 1256, "CodeRabbit": 1249}
    table2 = {
        "Agent": (33549, 23999, 71.5, 19.43),
        "Human": (6503, 5019, 77.2, 63.89),
    }
    return {
        "p2_table1": [_comparison("Ước tính tiếp nhận bảo thủ", {"count": 28418, "out_of": 128018, "pct": 22.2}, latest={"count": p2_adopters, "out_of": p2_latest, "pct": adoption}), _comparison("Ước tính tiếp nhận cao", {"count": 36687, "out_of": 128018, "pct": 28.66}, latest={"count": p2_adopters, "out_of": p2_latest, "pct": adoption})],
        "p2_tools": [_comparison(tool, {"repos": count}, latest={"repos": latest_tools.get(tool)}) for tool, count in tools_paper.items()],
        "p3_table2": [_comparison(name, {"prs": paper[0], "merged": paper[1], "merge_rate_pct": paper[2], "ttm_mean_h": paper[3]}, reproduced={"prs": reproduced.get(f"{name}_prs"), "merged": reproduced.get(f"{name}_merged"), "merge_rate_pct": reproduced.get(f"{name}_merge_rate"), "ttm_mean_h": reproduced.get(f"{name}_ttm_mean_h")}, latest=per_key[name]["2026"]) for name, paper in table2.items()],
        "p3_table3": [_comparison("Agent trong repo ≥500 sao", {"prs": 12344, "merged": 6766, "merge_rate_pct": 54.8, "ttm_mean_h": 46.03}, reproduced={"prs": reproduced.get("stars500_Agent_prs"), "merged": reproduced.get("stars500_Agent_merged"), "merge_rate_pct": reproduced.get("stars500_Agent_merge_rate"), "ttm_mean_h": reproduced.get("stars500_Agent_ttm_mean_h")})],
        "p3_table4": [_comparison(name, {"prs": paper[0], "merged": paper[1], "merge_rate_pct": paper[2], "ttm_mean_h": paper[3]}, reproduced={"prs": reproduced.get(f"{name}_prs"), "merged": reproduced.get(f"{name}_merged"), "merge_rate_pct": reproduced.get(f"{name}_merge_rate"), "ttm_mean_h": reproduced.get(f"{name}_ttm_mean_h")}, latest=per_key[name]["2026"]) for name, paper in table4_paper.items()],
        "p3_table5": [_comparison(f"{category} · {author}", {"prs": paper[0], "merged": paper[1], "merge_rate_pct": paper[2]}, reproduced={"prs": reproduced.get(f"task|{category}|{author}|prs"), "merged": reproduced.get(f"task|{category}|{author}|merged"), "merge_rate_pct": reproduced.get(f"task|{category}|{author}|merge_rate")}, latest={"merge_rate_pct": tasks.get(category, {}).get(author)}) for category, authors in table5_paper.items() for author, paper in authors.items()],
        "p3_table6_paper_only": [_comparison(metric, {"Agent": values[0], "Human": values[1]}) for metric, values in liwc.items()],
        "p3_table7": [_comparison("Agent", {"bot_pct": 61.46, "human_pct": 38.54}, latest={"bot_pct": comments.get("Agent")}), _comparison("Human", {"bot_pct": 51.42, "human_pct": 48.58}, latest={"bot_pct": comments.get("Human")})],
    }


def export(out: str | Path | None = None):
    from .baseline import REFERENCES, VALUES
    from .config import DATA_DIR
    from .db import connect, init_schema
    init_schema()
    output = Path(out) if out else DATA_DIR / "snapshots"; output.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        p2db, p3db, gdb = (stack.enter_context(connect(name)) for name in ("p2", "p3", "global"))
        latest = [date.fromisoformat(str(value)[:10]) for value in (_one(p2db, "SELECT MAX(adoption_date) FROM p2_repo WHERE adoption_date < '2030'"), _one(p3db, "SELECT MAX(created_at) FROM p3_pr"), _one(gdb, "SELECT MAX(fetched_at) FROM gs_count")) if value]
        ytd = max(latest) if latest else date.today(); months = _months(_cfg("START_MONTH", "2024-01"), ytd); years = [2024, 2025, 2026]
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
        provisional = [month_2026[n] for n, i in enumerate(indexes) if p3s["provisional"][i]]
        rows = []
        cumulative = ps["cumulative_adopters"]
        new_adopters = [
            cumulative[i] - (cumulative[i - 1] if i else 0)
            for i in indexes
        ]
        p2_low = [month_2026[n] for n, i in enumerate(indexes) if ps["denominator"][i] < 1000]
        rows.append(_row("p2_new_adopters", "p2", "Repo tiếp nhận mới", "repo", month_2026, new_adopters, [ps["denominator"][i] for i in indexes], low_n=p2_low, source_ids=["P2-06"]))
        rows.append(_row("p2_adoption_rate", "p2", "Tỷ lệ tiếp nhận tích lũy", "%", month_2026, [ps["adoption_rate_pct"][i] for i in indexes], [ps["denominator"][i] for i in indexes], low_n=p2_low, source_ids=["P2-06"]))
        rows.append(_row("p2_ai_commit_share", "p2", "Tỷ trọng commit AI-assisted", "%", month_2026, [ps["ai_commit_share_pct"][i] for i in indexes], source_ids=["P2-10"]))
        tool_aliases = {"Copilot": "Copilot", "Claude Code": "Claude Code", "Cursor": "Cursor", "Codex": "Codex", "Generic": "Generic", "Gemini": "Gemini"}
        tool_series = {key.casefold(): value for key, value in ps["new_adopters_by_tool"].items()}
        for tool, label in tool_aliases.items():
            values = tool_series.get(tool.casefold(), [0] * len(months))
            rows.append(_row(f"p2_new_{tool.lower().replace(' ', '_')}", "p2", f"Repo tiếp nhận mới: {label}", "repo", month_2026, [values[i] for i in indexes], source_ids=["P2-15"]))
        for agent_name in p3.AGENTS:
            counts = p3s["prs"][agent_name]
            rows.append(_row(f"p3_prs_{agent_name.lower().replace(' ', '_')}", "p3", f"PR {agent_name}", "PR", month_2026, [counts[i] for i in indexes], [counts[i] for i in indexes], provisional, [month_2026[n] for n, i in enumerate(indexes) if (counts[i] or 0) < 30], ["P3-02"]))
        for key in ("Agent", "Human", *p3.AGENTS):
            counts = p3s["prs"][key]
            rows.append(_row(f"p3_merge_rate_{key.replace(' ', '_')}", "p3", f"Tỷ lệ merge {key}", "%", month_2026, [p3s["merge_rate_pct"][key][i] for i in indexes], [counts[i] for i in indexes], provisional, [month_2026[n] for n, i in enumerate(indexes) if (counts[i] or 0) < 30], ["P3-06"]))
        for metric, label in (("ttm_mean_h", "TTM trung bình"), ("ttm_median_h", "TTM trung vị")):
            for key in ("Agent", "Human"):
                counts = p3s["prs"][key]
                rows.append(_row(f"p3_{metric}_{key}", "p3", f"{label} {key}", "giờ", month_2026, [p3s[metric][key][i] for i in indexes], [counts[i] for i in indexes], provisional, [month_2026[n] for n, i in enumerate(indexes) if (counts[i] or 0) < 30], ["P3-06"]))
        for key in ("Agent", "Human"):
            bot_values = []
            bot_counts = []
            for month in month_2026:
                if key == "Agent":
                    condition = "class IN ('Codex','Devin','Copilot','Cursor','Claude Code')"
                else:
                    condition = "class='Human'"
                bot = _one(p3db, f"SELECT COALESCE(SUM(comments_bot),0) FROM p3_pr WHERE substr(created_at,1,7)=? AND {condition}", (month,)) or 0
                human_comments = _one(p3db, f"SELECT COALESCE(SUM(comments_human),0) FROM p3_pr WHERE substr(created_at,1,7)=? AND {condition}", (month,)) or 0
                total_comments = bot + human_comments
                bot_values.append(round(100 * bot / total_comments, 4) if total_comments else None)
                bot_counts.append(total_comments or None)
            rows.append(_row(f"p3_bot_comment_share_{key}", "p3", f"Tỷ lệ comment bot trên PR {key}", "%", month_2026, bot_values, bot_counts, provisional, [month for month, count in zip(month_2026, bot_counts) if (count or 0) < 30], ["P3-08"]))
        for query_id in ("all", "copilot", "codex", "devin", "cursor", "claude_code", "jules"):
            values = gs["created"].get(query_id, [None] * len(months))
            rows.append(_row(f"gl_created_{query_id}", "global", f"PR tạo mới: {query_id}", "PR", month_2026, [values[i] for i in indexes], source_ids=["P3-02"]))
        rows.append(_row("gl_agent_share", "global", "Tỷ trọng PR agent", "%", month_2026, [gs["agent_share_pct"][i] for i in indexes], source_ids=["P3-02"]))
        _dump(output, "meta", meta); _dump(output, "baseline", {"references": REFERENCES, "values": [value.__dict__ for value in VALUES], "checks": {"p2": checks(p2db, "p2_check"), "p3": checks(p3db, "p3_baseline_check")}}); _dump(output, "series", {"months": months, "p2": ps, "p3": p3s, "global": gs}); _dump(output, "yearly", {"years": years, "ytd_until": ytd.isoformat(), "p2": p2.yearly(p2db, years, ytd), "p3": p3.yearly(p3db, years, ytd), "global": global_.yearly(gdb, years)}); _dump(output, "monthly_2026", {"months": month_2026, "rows": rows}); _dump(output, "paper_vs_latest", _comparisons(p2db, p3db))
    return output
