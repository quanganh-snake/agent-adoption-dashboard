from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class BaselineValue:
 id:str; paper:str; locator_vi:str; metric_vi:str; value:float; unit:str; n:int|None=None; note_vi:str=""
REFERENCES=[
"[2] R. Robbes, T. Matricon, T. Degueule, A. Hora, and S. Zacchiroli, “Agentic Much? Adoption of Coding Agents on GitHub,” ACM Transactions on Software Engineering and Methodology, 2026, doi: 10.1145/3822180.",
"[3] A. O. Njoku, Z. Sharafi, and F. Khomh, “When Code Authors Are Agents: A Large-Scale Study of Human–Agent Collaboration in Pull Requests,” AIware 2026, 2026, doi: 10.1145/3805760.3814909.",
"[4] R. Robbes et al., “agent-impact,” GitHub repository, 2026.","[5] R. Robbes et al., replication dataset, Zenodo, doi: 10.5281/zenodo.19256968.","[6] SENSE Research Lab, “Human-Agent-Collaboration,” GitHub repository, 2026.","[7] Artifacts for When Code Authors Are Agents, Zenodo, doi: 10.5281/zenodo.19098786."]
VALUES=(BaselineValue("P2-06","[2]","[2] Mục 5.3, Bảng 1","Ước tính bảo thủ",22.20,"%",128018),BaselineValue("P2-06","[2]","[2] Mục 5.3, Bảng 1","Ước tính cao",28.66,"%",128018),BaselineValue("P2-10","[2]","[2] Mục 9, Hình 11","Trung vị dòng thêm AI",31,"dòng"),BaselineValue("P3-06","[3]","[3] Mục 3.1, Bảng 2","Tỷ lệ merge Agent",71.5,"%",33549),BaselineValue("P3-06","[3]","[3] Mục 3.1, Bảng 2","Tỷ lệ merge Human",77.2,"%",6503),BaselineValue("P3-06","[3]","[3] Mục 3.1, Bảng 2","TTM Agent",19.43,"giờ",23999),BaselineValue("P3-06","[3]","[3] Mục 3.1, Bảng 2","TTM Human",63.89,"giờ",5019,"Churn enrichment live là additions + deletions của diff cuối, không phải tổng mọi commit."))
