from datetime import date
import sqlite3

import pytest

from agentdash.metrics.p2 import adoption_estimate, histogram_bin, histogram_median, series
from agentdash.sources.p3_classify import classify_pr
from agentdash.sources.taskclass import regex_task


def test_adoption_estimate():
    result = adoption_estimate(15_467, 9_440, 12_951, 128_018)
    assert result["conservative_pct"] == pytest.approx(22.20, abs=0.01)
    assert result["high_pct"] == pytest.approx(28.66, abs=0.01)


@pytest.mark.parametrize(
    ("login", "author_type", "head", "body", "expected"),
    [
        ("Copilot", "Bot", "copilot/fix-1", "", "Copilot"),
        ("alice", "User", "codex/x", "", "Codex"),
        ("alice", "User", "feature/x", "Co-Authored-By: Claude <noreply@anthropic.com>", "Claude Code"),
        ("devin-ai-integration", "Bot", "feature/x", "", "Devin"),
        ("dependabot", "Bot", "dependabot/npm", "", "Bot"),
        ("alice", "User", "feature/x", "", "Human"),
        ("alice", "User", "claude/x", "", "OtherAI"),
    ],
)
def test_classify_pr(login, author_type, head, body, expected):
    assert classify_pr(login, author_type, head, body) == expected


@pytest.mark.parametrize(
    ("title", "expected"),
    [("feat(ui)!: add", "feat"), ("Fix: bug", "fix"), ("Feature: x", None), ("chore", "chore")],
)
def test_task_regex(title, expected):
    assert regex_task(title) == expected


def test_histogram_helpers():
    assert histogram_median({1: 2, 11: 3, 31: 4}) == 11
    assert histogram_bin(1000) == 1000
    assert histogram_bin(1024) == 1010


def test_denominator_respects_as_of():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE p2_repo(repo TEXT, as_of TEXT, adoption_date TEXT, is_dotfiles INTEGER, error TEXT);
        CREATE TABLE p2_tool_adoption(repo TEXT, tool TEXT, adoption_date TEXT);
        CREATE TABLE p2_commit_month(repo TEXT, month TEXT, auth_type TEXT, tool TEXT, n INTEGER);
        """
    )
    db.execute("INSERT INTO p2_repo VALUES ('o/r','2026-02-21','2026-01-10',0,NULL)")
    result = series(db, ["2026-01", "2026-03"], date(2026, 3, 20))
    assert result["denominator"] == [1, 0]
