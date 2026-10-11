from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd

from ..config import DATA_DIR
from ..db import connect
from .taskclass import TASK_CATEGORY_MAP

FILES = ("pull_request", "repository", "pr_task_type", "human_pull_request", "human_pr_task_type")
BASE = "https://huggingface.co/datasets/hao-li/AIDev/resolve/v3/"
AGENT_LABELS = {
    "OpenAI_Codex": "Codex",
    "Devin": "Devin",
    "Copilot": "Copilot",
    "Cursor": "Cursor",
    "Claude_Code": "Claude Code",
}
PAPER = {
    "Agent_prs": 33_549, "Agent_merged": 23_999, "Agent_merge_rate": 71.5, "Agent_ttm_mean_h": 19.43,
    "Human_prs": 6_503, "Human_merged": 5_019, "Human_merge_rate": 77.2, "Human_ttm_mean_h": 63.89,
    "stars500_Agent_prs": 12_344, "stars500_Agent_merged": 6_766, "stars500_Agent_merge_rate": 54.8,
    "stars500_Agent_ttm_mean_h": 46.03,
    "Codex_prs": 4_297, "Codex_merged": 2_833, "Codex_merge_rate": 65.9, "Codex_ttm_mean_h": 32.54,
    "Devin_prs": 3_485, "Devin_merged": 1_811, "Devin_merge_rate": 52.0, "Devin_ttm_mean_h": 43.13,
    "Copilot_prs": 3_368, "Copilot_merged": 1_425, "Copilot_merge_rate": 42.3, "Copilot_ttm_mean_h": 85.40,
    "Cursor_prs": 918, "Cursor_merged": 567, "Cursor_merge_rate": 61.8, "Cursor_ttm_mean_h": 24.52,
    "Claude Code_prs": 276, "Claude Code_merged": 130, "Claude Code_merge_rate": 47.1,
    "Claude Code_ttm_mean_h": 42.92,
}
TASK_PAPER = {
    ("Docs & Style", "Agent"): (4_075, 3_413, 83.8), ("Docs & Style", "Human"): (578, 450, 77.9),
    ("Feature & Behavior", "Agent"): (22_896, 15_725, 68.7), ("Feature & Behavior", "Human"): (3_812, 2_952, 77.4),
    ("Infrastructure", "Agent"): (1_934, 1_410, 72.9), ("Infrastructure", "Human"): (1_561, 1_202, 77.0),
    ("Internal Quality", "Agent"): (4_644, 3_451, 74.3), ("Internal Quality", "Human"): (552, 415, 75.2),
}


def download_aidev() -> Path:
    cache = DATA_DIR / "cache" / "aidev-v3"
    cache.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = cache / f"{name}.parquet"
        if not target.exists():
            urllib.request.urlretrieve(BASE + target.name, target)
    return cache


def _metrics(frame: pd.DataFrame) -> dict[str, float]:
    merged = frame["merged_at"].notna()
    created_at = pd.to_datetime(frame.loc[merged, "created_at"], utc=True)
    merged_at = pd.to_datetime(frame.loc[merged, "merged_at"], utc=True)
    ttm = (merged_at - created_at).dt.total_seconds().div(3600)
    return {
        "prs": float(len(frame)),
        "merged": float(merged.sum()),
        "merge_rate": float(100 * merged.mean()),
        "ttm_mean_h": float(ttm.mean()),
    }


def _repo_name(url: str) -> str:
    return str(url).removeprefix("https://api.github.com/repos/").removeprefix("https://github.com/")


def reproduce_baseline() -> dict[str, float]:
    cache = download_aidev()
    agent_all = pd.read_parquet(cache / "pull_request.parquet")
    human = pd.read_parquet(cache / "human_pull_request.parquet")
    repos = pd.read_parquet(cache / "repository.parquet")
    agent_tasks = pd.read_parquet(cache / "pr_task_type.parquet")[["id", "type"]]
    human_tasks = pd.read_parquet(cache / "human_pr_task_type.parquet")[["id", "type"]]

    agent_all = agent_all.merge(agent_tasks, on="id", how="inner")
    human = human.merge(human_tasks, on="id", how="inner")
    agent = agent_all[~agent_all["type"].isin(("other", "revert"))].copy()
    human = human[~human["type"].isin(("other", "revert"))].copy()
    agent["author_group"] = "Agent"
    human["author_group"] = "Human"
    agent["repo"] = agent["repo_url"].map(_repo_name)
    human["repo"] = human["repo_url"].map(_repo_name)
    stars = dict(zip(repos["full_name"], repos["stars"]))
    agent["stars"] = agent["repo"].map(stars)
    agent_all["repo"] = agent_all["repo_url"].map(_repo_name)
    agent_all["stars"] = agent_all["repo"].map(stars)

    results: dict[str, float] = {}
    for label, frame in (("Agent", agent), ("Human", human)):
        for metric, value in _metrics(frame).items():
            results[f"{label}_{metric}"] = value

    # The artifact's robustness panel includes repositories at the 500-star boundary.
    stars500 = agent[agent["stars"] >= 500]
    for metric, value in _metrics(stars500).items():
        results[f"stars500_Agent_{metric}"] = value
    for raw_name, display_name in AGENT_LABELS.items():
        frame = stars500[stars500["agent"] == raw_name]
        for metric, value in _metrics(frame).items():
            results[f"{display_name}_{metric}"] = value

    combined = pd.concat((agent, human), ignore_index=True)
    combined["task_category"] = combined["type"].map(TASK_CATEGORY_MAP)
    for (category, author), frame in combined.groupby(["task_category", "author_group"], dropna=True):
        values = _metrics(frame)
        results[f"task|{category}|{author}|prs"] = values["prs"]
        results[f"task|{category}|{author}|merged"] = values["merged"]
        results[f"task|{category}|{author}|merge_rate"] = values["merge_rate"]

    with connect("p3") as con:
        con.executemany(
            "INSERT OR REPLACE INTO p3_repo(repo,stars,human_baseline) VALUES(?,?,?)",
            [(row.full_name, int(row.stars), int(row.stars > 500)) for row in repos.itertuples()],
        )
        for metric, reproduced in results.items():
            if metric.startswith("task|"):
                _, category, author, field = metric.split("|")
                index = {"prs": 0, "merged": 1, "merge_rate": 2}[field]
                paper = TASK_PAPER[(category, author)][index]
            else:
                paper = PAPER.get(metric)
            con.execute(
                "INSERT OR REPLACE INTO p3_baseline_check(metric,paper,reproduced) VALUES(?,?,?)",
                (metric, paper, reproduced),
            )
        con.commit()

    print("Chỉ số\tBài báo\tTái lập\tTrạng thái")
    for metric, paper in {**PAPER, **{f"task|{c}|{a}|merge_rate": v[2] for (c, a), v in TASK_PAPER.items()}}.items():
        reproduced = results[metric]
        tolerance = 0.1
        status = "OK" if abs(reproduced - paper) <= tolerance else "LỆCH"
        print(f"{metric}\t{paper}\t{reproduced:.2f}\t{status}")
    return results
