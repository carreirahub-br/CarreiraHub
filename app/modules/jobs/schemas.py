from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class JobCard:
    slug: str
    title: str
    company_name: str
    city: str
    state: str
    work_mode: str
    work_mode_label: str
    contract_type: str
    salary_text: str | None
    published_at: datetime | None
    category_slug: str = ""
    is_demo: bool = False

    @property
    def location_label(self) -> str:
        if self.work_mode == "remote" and not self.city:
            return "Remoto"
        parts = [part for part in (self.city, self.state) if part]
        return " / ".join(parts) if parts else "Local não informado"

    @property
    def detail_path(self) -> str:
        return f"/vagas/{self.slug}"
