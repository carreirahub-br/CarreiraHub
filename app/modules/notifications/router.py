from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_csrf
from app.core.templating import templates
from app.modules.notifications.service import (
    INTEREST_OPTIONS,
    AlertFormError,
    subscribe_alert,
)

router = APIRouter()


def _form_context(
    request: Request,
    *,
    email: str = "",
    interest_area: str = "todas",
    error: str | None = None,
    success: bool = False,
):
    return {
        "request": request,
        "email": email,
        "interest_area": interest_area,
        "interest_options": INTEREST_OPTIONS,
        "error": error,
        "success": success,
    }


@router.post("/alertas", include_in_schema=False)
async def create_alert(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
):
    form = await request.form()
    email = str(form.get("email") or "")
    interest_area = str(form.get("interest_area") or "todas")
    consent = str(form.get("consent") or "") in {"1", "on", "true", "sim"}
    try:
        subscribe_alert(db, email=email, interest_area=interest_area, consent=consent)
        context = _form_context(request, success=True)
    except AlertFormError as exc:
        context = _form_context(
            request,
            email=email,
            interest_area=interest_area,
            error=exc.message,
        )
    template = "components/alert_form.html"
    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse(request, template, context)
    return templates.TemplateResponse(
        request,
        "pages/alert_result.html",
        {
            **context,
            "meta_title": "Alerta de vagas | CarreiraHub",
            "meta_description": "Inscrição em alertas de vagas do CarreiraHub.",
            "canonical_path": "/alertas",
        },
    )
