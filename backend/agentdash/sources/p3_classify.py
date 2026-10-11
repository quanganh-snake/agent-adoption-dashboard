from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

PATTERN_DIR = Path(__file__).resolve().parents[3] / "vendor" / "agent-impact" / "config" / "patterns"

def _patterns(name: str) -> re.Pattern[str]:
    with (PATTERN_DIR / f"{name}.csv").open(encoding="utf-8", newline="") as handle:
        patterns = [row["pattern"].strip() for row in csv.DictReader(handle) if row["pattern"].strip()]
    return re.compile("|".join(f"(?:{pattern})" for pattern in patterns), re.IGNORECASE)

@lru_cache
def branch_patterns() -> re.Pattern[str]: return _patterns("branches")
@lru_cache
def author_patterns() -> re.Pattern[str]: return _patterns("authors")
@lru_cache
def bot_patterns() -> re.Pattern[str]: return _patterns("bots")

def classify_pr(author_login: str | None, author_type: str | None, head_ref: str | None, body: str | None) -> str:
    login, head, text = (author_login or "").lower(), head_ref or "", (body or "").lower()
    if head.lower().startswith("copilot/") and login in {"copilot", "copilot-swe-agent"}: return "Copilot"
    if login in {"devin-ai-integration", "devin-ai-integration[bot]"}: return "Devin"
    if login in {"google-labs-jules", "google-labs-jules[bot]"}: return "Jules"
    if head.lower().startswith("codex/"): return "Codex"
    if head.lower().startswith("cursor/"): return "Cursor"
    if "co-authored-by: claude" in text: return "Claude Code"
    if branch_patterns().search(head) or author_patterns().search(author_login or ""): return "OtherAI"
    if author_type == "Bot" or bot_patterns().search(author_login or ""): return "Bot"
    return "Human" if author_login else "Bot"
