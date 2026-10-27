from dataclasses import dataclass, field
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
    description: str = ""

    @property
    def location_label(self) -> str:
        if self.work_mode == "remote" and not self.city:
            return "Remoto"
        parts = [part for part in (self.city, self.state) if part]
        return " / ".join(parts) if parts else "Local não informado"

    @property
    def detail_path(self) -> str:
        return f"/vagas/{self.slug}"


@dataclass
class PaginatedJobs:
    """
    Estrutura paginada que se comporta como lista para total compatibilidade,
    mas fornece metadados e controles para a interface web.
    """
    items: list[JobCard] = field(default_factory=list)
    total: int = 0
    page: int = 1
    per_page: int = 10
    total_pages: int = 1

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]

    def __bool__(self) -> bool:
        return bool(self.items)

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def prev_page(self) -> int:
        return max(1, self.page - 1)

    @property
    def next_page(self) -> int:
        return min(self.total_pages, self.page + 1)

    @property
    def page_range(self) -> list[int]:
        """Gera uma lista de até 5 páginas centrada na página corrente."""
        if self.total_pages <= 7:
            return list(range(1, self.total_pages + 1))
        start = max(1, self.page - 2)
        end = min(self.total_pages, self.page + 2)
        if start == 1:
            end = min(self.total_pages, 5)
        elif end == self.total_pages:
            start = max(1, self.total_pages - 4)
        return list(range(start, end + 1))

    @property
    def showing_start(self) -> int:
        if self.total == 0:
            return 0
        return (self.page - 1) * self.per_page + 1

    @property
    def showing_end(self) -> int:
        return min(self.page * self.per_page, self.total)
