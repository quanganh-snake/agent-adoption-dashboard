from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data")).expanduser()
AGENT_IMPACT_COMMIT = "69b95b6d92f19adaee7d2720ccf81dd00a205cbf"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ROLE = os.getenv("AGENTDASH_ROLE", "local-all")
STATE_RELEASE_REPO = os.getenv("STATE_RELEASE_REPO", "quanganh-snake/agent-adoption-dashboard")
P2_CHUNK_SIZE = int(os.getenv("P2_CHUNK_SIZE", "200"))
P2_WORKERS = int(os.getenv("P2_WORKERS", "8"))
P3_HUMAN_ENRICH_PCT = int(os.getenv("P3_HUMAN_ENRICH_PCT", "10"))
START_MONTH = os.getenv("START_MONTH", "2024-01")


def github_tokens() -> list[str]:
    configured = [value.strip() for value in os.getenv("GITHUB_TOKENS", "").split(",") if value.strip()]
    if configured:
        return configured
    try:
        token = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=False
        ).stdout.strip()
    except OSError:
        token = ""
    if token:
        return [token]
    raise RuntimeError("Thiếu GitHub token: đặt GITHUB_TOKENS hoặc chạy gh auth login")
