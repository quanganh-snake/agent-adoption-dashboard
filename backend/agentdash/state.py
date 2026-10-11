"""GitHub Release transport for the durable SQLite state."""
from __future__ import annotations

import gzip
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

from .config import DATA_DIR, STATE_RELEASE_REPO


def _sources(sources: str | list[str]) -> list[str]:
    values = sources.split(",") if isinstance(sources, str) else sources
    result = [value.strip() for value in values if value.strip()]
    unknown = set(result) - {"p2", "p3", "global"}
    if unknown:
        raise ValueError(f"Nguồn state không hợp lệ: {', '.join(sorted(unknown))}")
    return result


def pull(sources: str | list[str]) -> None:
    """Download available state assets from the `state` release."""
    state = DATA_DIR / "state"
    state.mkdir(parents=True, exist_ok=True)
    for source in _sources(sources):
        asset = f"{source}.db.gz"
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            result = subprocess.run(
                ["gh", "release", "download", "state", "--repo", STATE_RELEASE_REPO, "--pattern", asset, "--dir", str(work)],
                capture_output=True,
                text=True,
                check=False,
            )
            compressed = work / asset
            if result.returncode and not compressed.exists():
                continue
            with gzip.open(compressed, "rb") as input_file, (state / f"{source}.db").open("wb") as output_file:
                shutil.copyfileobj(input_file, output_file)


def push(sources: str | list[str]) -> None:
    """Compress and replace the requested assets in the `state` release."""
    state = DATA_DIR / "state"
    for source in _sources(sources):
        database = state / f"{source}.db"
        if not database.is_file():
            raise FileNotFoundError(database)
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / f"{source}.db"
            with sqlite3.connect(database) as source_db, sqlite3.connect(snapshot) as target_db:
                source_db.backup(target_db)
            asset = Path(directory) / f"{source}.db.gz"
            with snapshot.open("rb") as input_file, gzip.open(asset, "wb") as output_file:
                shutil.copyfileobj(input_file, output_file)
            release = subprocess.run(["gh", "release", "view", "state", "--repo", STATE_RELEASE_REPO], capture_output=True, check=False)
            if release.returncode:
                subprocess.run(["gh", "release", "create", "state", "--repo", STATE_RELEASE_REPO, "--title", "State", "--notes", "SQLite state assets"], check=True)
            subprocess.run(["gh", "release", "upload", "state", str(asset), "--repo", STATE_RELEASE_REPO, "--clobber"], check=True)
