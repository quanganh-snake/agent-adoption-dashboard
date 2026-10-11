from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineValue:
    id: str
    paper: str
    locator_vi: str
    metric_vi: str
    value: float
    unit: str
    n: int | None = None
    note_vi: str = ""


REFERENCES = [
    {"id": "2", "text": "[2] R. Robbes et al., “Agentic Much? Adoption of Coding Agents on GitHub,” ACM TOSEM, 2026.", "doi_url": "https://doi.org/10.1145/3822180", "code_url": "https://github.com/labri-progress/agent-impact", "data_url": "https://doi.org/10.5281/zenodo.19256968"},
    {"id": "3", "text": "[3] A. O. Njoku, Z. Sharafi, and F. Khomh, “When Code Authors Are Agents,” AIware 2026.", "doi_url": "https://doi.org/10.1145/3805760.3814909", "code_url": "https://github.com/SENSE-Research-Lab/Human-Agent-Collaboration", "data_url": "https://doi.org/10.5281/zenodo.19098786"},
    {"id": "4", "text": "[4] R. Robbes et al., agent-impact, GitHub repository, 2026.", "code_url": "https://github.com/labri-progress/agent-impact"},
    {"id": "5", "text": "[5] Agentic Much? replication dataset, Zenodo, 2026.", "data_url": "https://doi.org/10.5281/zenodo.19256968"},
    {"id": "6", "text": "[6] SENSE Research Lab, Human-Agent-Collaboration, GitHub repository, 2026.", "code_url": "https://github.com/SENSE-Research-Lab/Human-Agent-Collaboration"},
    {"id": "7", "text": "[7] Artifacts for When Code Authors Are Agents, Zenodo, 2026.", "data_url": "https://doi.org/10.5281/zenodo.19098786"},
]


def value(identifier, paper, locator, metric, amount, unit, n=None, note=""):
    return BaselineValue(identifier, paper, locator, metric, amount, unit, n, note)


VALUES = (
    value("P2-05", "[2]", "[2] Abstract; Mục 5", "Repository phân tích", 128_018, "repo"),
    value("P2-06", "[2]", "[2] Mục 5.3, Bảng 1", "Ước tính tiếp nhận bảo thủ", 22.20, "%", 128_018, "Tỷ lệ repository có dấu vết tiếp nhận; không phải tỷ lệ code do AI viết."),
    value("P2-06", "[2]", "[2] Mục 5.3, Bảng 1", "Ước tính tiếp nhận cao", 28.66, "%", 128_018, "Ngoại suy thô; không phải tỷ lệ code do AI viết."),
    value("P2-07", "[2]", "[2] Mục 5, Bảng 1", "Dấu vết file-level", 15_467, "repo", 128_018),
    value("P2-07", "[2]", "[2] Mục 5, Bảng 1", "Dấu vết commit-only", 12_951, "repo", 112_551),
    value("P2-15", "[2]", "[2] Mục 8.2, Hình 8", "Repo adopter tích lũy", 26_883, "repo"),
    value("P2-15", "[2]", "[2] Mục 8.2, Hình 8", "Copilot", 13_890, "repo"),
    value("P2-15", "[2]", "[2] Mục 8.2, Hình 8", "Claude Code", 12_053, "repo"),
    value("P2-15", "[2]", "[2] Mục 8.2, Hình 8", "Cursor", 2_965, "repo"),
    value("P2-15", "[2]", "[2] Mục 8.2, Hình 8", "Codex", 2_147, "repo"),
    value("P2-10", "[2]", "[2] Mục 9, Hình 11", "Trung vị dòng thêm AI-assisted", 31, "dòng"),
    value("P2-10", "[2]", "[2] Mục 9, Hình 11", "Trung vị dòng thêm Human", 11, "dòng"),
    value("P2-10", "[2]", "[2] Mục 9, Hình 11", "Trung vị dòng thêm Bot", 4, "dòng"),
    value("P3-02", "[3]", "[3] Abstract", "Agent-authored PR", 33_596, "PR", 2_807),
    value("P3-02", "[3]", "[3] Abstract", "Human-authored PR", 6_618, "PR", 2_807),
    value("P3-06", "[3]", "[3] Mục 3.1, Bảng 2", "Tỷ lệ merge Agent", 71.5, "%", 33_549),
    value("P3-06", "[3]", "[3] Mục 3.1, Bảng 2", "Tỷ lệ merge Human", 77.2, "%", 6_503),
    value("P3-06", "[3]", "[3] Mục 3.1, Bảng 2", "TTM trung bình Agent", 19.43, "giờ", 23_999, "Chỉ tính trên PR đã merge."),
    value("P3-06", "[3]", "[3] Mục 3.1, Bảng 2", "TTM trung bình Human", 63.89, "giờ", 5_019, "Chỉ tính trên PR đã merge."),
    value("P3-07", "[3]", "[3] Mục 3.2.1, Bảng 5", "Merge rate Docs & Style Agent", 83.8, "%", 4_075),
    value("P3-08", "[3]", "[3] Mục 3.3, Bảng 7", "Comment bot trên PR Agent", 61.46, "%"),
    value("P3-08", "[3]", "[3] Mục 3.3, Bảng 7", "Comment bot trên PR Human", 51.42, "%"),
)
