from __future__ import annotations

import csv
import hashlib
import io
import re
import tarfile
from pathlib import Path

import httpx

from ..config import DATA_DIR
from .p2_ingest import ingest_project

URL = "https://zenodo.org/records/19256968/files/feb-21.tar.gz"
MD5 = "6dde657b209565269924a3445d2ea455"
CATEGORIES = {
    "tool_commit_adopters", "tool_only_adopters", "ignored_tools_commit_adopters",
    "commit_only_adopters", "ignored_tools_only_adopters", "non_adopters",
}
PROJECT_FILE_RE = re.compile(
    rf"(?:^|/)({'|'.join(CATEGORIES)})/([^/]+)/(adoption_dates\.csv|commit_stats_main\.csv|commit_stats_files\.csv)$"
)


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def download() -> Path:
    path = DATA_DIR / "cache/zenodo/feb-21.tar.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    start = path.stat().st_size if path.exists() else 0
    headers = {"Range": f"bytes={start}-"} if start else {}
    with httpx.stream("GET", URL, headers=headers, follow_redirects=True, timeout=None) as response:
        response.raise_for_status()
        append = start > 0 and response.status_code == 206
        with path.open("ab" if append else "wb") as output:
            for chunk in response.iter_bytes(8 * 1024 * 1024):
                output.write(chunk)
    if _md5(path) != MD5:
        path.unlink()
        raise RuntimeError("Zenodo md5 không khớp")
    return path


def _latest_report(path: Path) -> dict[str, dict[str, str]]:
    latest_number = -1
    latest_content = ""
    with tarfile.open(path, "r|gz") as archive:
        for member in archive:
            match = re.search(r"analysis_report_(\d+)\.csv$", member.name)
            if not match or not member.isfile():
                continue
            number = int(match.group(1))
            extracted = archive.extractfile(member)
            if number > latest_number and extracted:
                latest_number = number
                latest_content = extracted.read().decode("utf-8", errors="replace")
    return {
        row.get("github_url", "").removeprefix("https://github.com/").removesuffix(".git"): row
        for row in csv.DictReader(io.StringIO(latest_content))
        if row.get("github_url")
    }


def _report_indexes(report: dict[str, dict[str, str]]) -> tuple[dict[str, str], dict[str, str]]:
    by_path: dict[str, str] = {}
    by_folder: dict[str, str] = {}
    for repo, row in report.items():
        for field in ("path", "log_path"):
            value = row.get(field) or ""
            if value:
                by_path[Path(value).name] = repo
        by_folder[repo.replace("/", "-")] = repo
    return by_path, by_folder


def ingest_zenodo(keep: bool = False) -> None:
    path = download()
    report = _latest_report(path)
    by_path, by_folder = _report_indexes(report)
    current: tuple[str, str] | None = None
    files: dict[str, bytes] = {}

    def flush() -> None:
        nonlocal files
        if current is None or not files:
            return
        category, folder = current
        repo = by_path.get(folder) or by_folder.get(folder) or folder
        ingest_project(repo, category, files, "zenodo", None, "2026-02-21", report.get(repo))
        files = {}

    try:
        with tarfile.open(path, "r|gz") as archive:
            for member in archive:
                match = PROJECT_FILE_RE.search(member.name)
                if not match or not member.isfile():
                    continue
                category, folder, filename = match.groups()
                key = (category, folder)
                if current != key:
                    flush()
                    current = key
                extracted = archive.extractfile(member)
                if extracted:
                    files[filename] = extracted.read()
            flush()
    finally:
        if not keep and path.exists():
            path.unlink()


def ingest_output_tree(root: Path, source: str, pass_id: int | None, as_of: str) -> None:
    reports = sorted(
        root.rglob("analysis_report_*.csv"),
        key=lambda item: int(re.search(r"_(\d+)\.csv$", item.name).group(1)),
    )
    report_by_repo: dict[str, dict[str, str]] = {}
    if reports:
        with reports[-1].open(encoding="utf-8", newline="") as handle:
            report_by_repo = {
                row.get("github_url", "").removeprefix("https://github.com/").removesuffix(".git"): row
                for row in csv.DictReader(handle)
            }
    _, by_folder = _report_indexes(report_by_repo)
    for category_name in CATEGORIES:
        for category in root.rglob(category_name):
            if not category.is_dir():
                continue
            for project in category.iterdir():
                if not project.is_dir():
                    continue
                files = {
                    item.name: item.read_bytes()
                    for item in project.iterdir()
                    if item.name in {"adoption_dates.csv", "commit_stats_main.csv", "commit_stats_files.csv"}
                }
                if not files:
                    continue
                repo = by_folder.get(project.name, project.name)
                ingest_project(repo, category.name, files, source, pass_id, as_of, report_by_repo.get(repo))
