from datetime import datetime, timezone

_MONTHS = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def format_date_br(value: datetime | None) -> str:
    if value is None:
        return ""
    return f"{value.day} de {_MONTHS[value.month - 1]} de {value.year}"


def format_relative_br(value: datetime | None, now: datetime | None = None) -> str:
    if value is None:
        return ""
    current = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    delta = current - value
    days = delta.days
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "agora"
    if seconds < 3600:
        minutes = seconds // 60
        return f"há {minutes} min"
    if days < 1:
        hours = seconds // 3600
        return f"há {hours} h"
    if days == 1:
        return "ontem"
    if days < 30:
        return f"há {days} dias"
    return format_date_br(value)
