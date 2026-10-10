from pathlib import Path

from markupsafe import Markup, escape
from starlette.requests import Request

from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.core.dates import format_date_br, format_relative_br
from app.core.security import ensure_csrf_token

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def request_context(request: Request) -> dict:
    settings = get_settings()
    canonical_path = getattr(request.state, "canonical_path", request.url.path)
    return {
        "csrf_token": ensure_csrf_token(request),
        "app_name": settings.app_name,
        "base_url": settings.base_url,
        "contact_email": settings.contact_email,
        "adsense_enabled": settings.adsense_enabled and bool(settings.adsense_client_id),
        "adsense_client_id": settings.adsense_client_id,
        "social_linkedin_url": settings.social_linkedin_url,
        "social_instagram_url": settings.social_instagram_url,
        "social_youtube_url": settings.social_youtube_url,
        "current_path": request.url.path,
        "canonical_url": f"{settings.base_url}{canonical_path}",
        "is_development": settings.is_development,
    }


def nl2br(value: str | None) -> Markup:
    if not value:
        return Markup("")
    return Markup("<br>\n".join(escape(value).splitlines()))


templates = Jinja2Templates(directory=str(TEMPLATES_DIR), context_processors=[request_context])
templates.env.filters["date_br"] = format_date_br
templates.env.filters["relative_br"] = format_relative_br
templates.env.filters["nl2br"] = nl2br
templates.env.autoescape = True
