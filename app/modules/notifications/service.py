import secrets

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.modules.jobs.service import CATEGORIES
from app.modules.notifications.models import JobAlert

INTEREST_OPTIONS = [{"slug": "todas", "name": "Todas as áreas"}, *CATEGORIES]
email_adapter = TypeAdapter(EmailStr)


class AlertFormError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def validate_email(value: str) -> str:
    try:
        return str(email_adapter.validate_python(value.strip().lower()))
    except ValidationError as exc:
        raise AlertFormError("Informe um e-mail válido.") from exc


def subscribe_alert(db: Session, *, email: str, interest_area: str, consent: bool) -> JobAlert:
    if not consent:
        raise AlertFormError("É necessário consentir com o envio de comunicações para continuar.")
    allowed = {item["slug"] for item in INTEREST_OPTIONS}
    area = interest_area if interest_area in allowed else "todas"
    normalized = validate_email(email)
    alert = JobAlert(
        email=normalized,
        interest_area=area,
        consent=True,
        confirmed=False,
        confirm_token=secrets.token_urlsafe(24),
    )
    try:
        db.add(alert)
        db.commit()
        db.refresh(alert)
    except Exception as exc:
        db.rollback()
        raise AlertFormError(
            "Não foi possível registrar o alerta agora. Tente novamente em instantes."
        ) from exc
    return alert
