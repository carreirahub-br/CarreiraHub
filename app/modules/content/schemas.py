from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ArticleCard:
    slug: str
    title: str
    excerpt: str
    category: str
    cover_image: str | None
    published_at: datetime | None

    @property
    def path(self) -> str:
        return f"/blog/{self.slug}"
