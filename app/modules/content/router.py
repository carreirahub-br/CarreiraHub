from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.templating import templates
from app.modules.content.service import get_article, recent_articles

router = APIRouter()


@router.get("/blog/{slug}", include_in_schema=False)
def article_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    article = get_article(db, slug)
    if article is None:
        return templates.TemplateResponse(
            request,
            "pages/placeholder.html",
            {
                "title": "Artigo não encontrado",
                "intro": "Este conteúdo não está publicado ou o endereço está incorreto.",
                "meta_title": "Artigo não encontrado | CarreiraHub",
                "meta_description": "Artigo indisponível no blog do CarreiraHub.",
                "canonical_path": f"/blog/{slug}",
            },
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "pages/article_detail.html",
        {
            "article": article,
            "related": recent_articles(db, limit=3),
            "meta_title": f"{article.title} | CarreiraHub",
            "meta_description": article.excerpt or article.title,
            "canonical_path": f"/blog/{article.slug}",
        },
    )
