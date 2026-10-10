from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.templating import templates
from app.modules.home.service import build_home_page

router = APIRouter()


@router.get("/", include_in_schema=False)
def home(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    page = build_home_page(db, settings)
    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {
            "page": page,
            "meta_title": "CarreiraHub — vagas, currículos e carreira",
            "meta_description": (
                "Encontre vagas de emprego, crie um currículo profissional e use ferramentas "
                "gratuitas para avançar na carreira. Conectando talentos a novas oportunidades."
            ),
            "canonical_path": "/",
            "og_type": "website",
        },
    )
