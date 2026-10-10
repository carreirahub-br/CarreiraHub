import secrets

from fastapi import HTTPException, Request, status


def ensure_csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


async def require_csrf(request: Request) -> None:
    expected = request.session.get("csrf_token")
    form = await request.form()
    provided = form.get("csrf_token")
    if not expected or not provided or not secrets.compare_digest(str(provided), str(expected)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Falha de validação CSRF.")
