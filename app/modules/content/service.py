from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.content.models import Article
from app.modules.content.schemas import ArticleCard


def recent_articles(db: Session, limit: int = 3) -> list[ArticleCard]:
    try:
        rows = db.scalars(
            select(Article)
            .where(Article.is_published.is_(True))
            .order_by(Article.published_at.desc().nullslast())
            .limit(limit)
        ).all()
    except Exception:
        return []
    return [
        ArticleCard(
            slug=article.slug,
            title=article.title,
            excerpt=article.excerpt,
            category=article.category,
            cover_image=article.cover_image,
            published_at=article.published_at,
        )
        for article in rows
    ]


def get_article(db: Session, slug: str) -> Article | None:
    try:
        return db.scalar(select(Article).where(Article.slug == slug, Article.is_published.is_(True)))
    except Exception:
        return None
