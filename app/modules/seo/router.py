from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response

from app.core.config import get_settings

router = APIRouter()


@router.get("/robots.txt", include_in_schema=False)
def robots(request: Request) -> PlainTextResponse:
    settings = get_settings()
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /entrar\n"
        "Disallow: /cadastrar\n"
        f"Sitemap: {settings.base_url}/sitemap.xml\n"
    )
    return PlainTextResponse(body)


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap() -> Response:
    settings = get_settings()
    base = settings.base_url
    paths = [
        "/",
        "/vagas",
        "/curriculo",
        "/ferramentas",
        "/blog",
        "/empresas",
        "/sobre",
        "/contato",
        "/como-funciona",
        "/termos",
        "/privacidade",
        "/cookies",
    ]
    urls = "\n".join(
        f"  <url><loc>{base}{path}</loc><changefreq>daily</changefreq></url>" for path in paths
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n"
    )
    return Response(content=xml, media_type="application/xml")
