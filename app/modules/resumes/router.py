from fastapi import APIRouter, Request

from app.core.templating import templates

router = APIRouter()


@router.get("/curriculo", include_in_schema=False)
def resume_builder(request: Request):
    return templates.TemplateResponse(
        request,
        "pages/resume_builder.html",
        {
            "meta_title": "Criar currículo grátis | CarreiraHub",
            "meta_description": (
                "Monte um currículo profissional gratuito, com pré-visualização em tempo real "
                "e exportação em PDF. Seus dados ficam apenas no seu navegador."
            ),
            "canonical_path": "/curriculo",
        },
    )
