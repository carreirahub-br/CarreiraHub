from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.jobs.models import Job
from app.modules.jobs.schemas import JobCard

WORK_MODE_LABELS = {
    "remote": "Remoto",
    "hybrid": "Híbrido",
    "onsite": "Presencial",
}

CATEGORIES = (
    {"slug": "tecnologia", "name": "Tecnologia", "icon": "code"},
    {"slug": "administracao", "name": "Administração", "icon": "clipboard"},
    {"slug": "marketing", "name": "Marketing", "icon": "megaphone"},
    {"slug": "financeiro", "name": "Financeiro", "icon": "wallet"},
    {"slug": "engenharia", "name": "Engenharia", "icon": "cog"},
    {"slug": "saude", "name": "Saúde", "icon": "heart"},
    {"slug": "logistica", "name": "Logística", "icon": "truck"},
    {"slug": "atendimento", "name": "Atendimento", "icon": "headset"},
)


def _to_card(job: Job, *, is_demo: bool = False) -> JobCard:
    return JobCard(
        slug=job.slug,
        title=job.title,
        company_name=job.company_name,
        city=job.city,
        state=job.state,
        work_mode=job.work_mode,
        work_mode_label=WORK_MODE_LABELS.get(job.work_mode, job.work_mode),
        contract_type=job.contract_type,
        salary_text=job.salary_text,
        published_at=job.published_at,
        category_slug=job.category_slug,
        is_demo=is_demo,
    )


def _demo_jobs() -> list[JobCard]:
    now = datetime.now(timezone.utc)
    samples = [
        ("analista-dados-remoto-demo", "Analista de Dados", "Empresa demonstração", "São Paulo", "SP", "remote", "CLT", "tecnologia", "A combinar", 1),
        ("assistente-administrativo-demo", "Assistente Administrativo", "Empresa demonstração", "Belo Horizonte", "MG", "hybrid", "CLT", "administracao", None, 2),
        ("estagio-marketing-demo", "Estágio em Marketing", "Empresa demonstração", "Curitiba", "PR", "onsite", "Estágio", "marketing", "Bolsa-auxílio", 3),
        ("desenvolvedor-python-demo", "Desenvolvedor Python Júnior", "Empresa demonstração", "", "", "remote", "PJ", "tecnologia", None, 4),
        ("analista-financeiro-demo", "Analista Financeiro", "Empresa demonstração", "Recife", "PE", "hybrid", "CLT", "financeiro", "A combinar", 5),
        ("atendente-suporte-demo", "Atendente de Suporte", "Empresa demonstração", "Porto Alegre", "RS", "onsite", "CLT", "atendimento", None, 6),
    ]
    cards: list[JobCard] = []
    for slug, title, company, city, state, mode, contract, category, salary, days in samples:
        cards.append(
            JobCard(
                slug=slug,
                title=title,
                company_name=company,
                city=city,
                state=state,
                work_mode=mode,
                work_mode_label=WORK_MODE_LABELS[mode],
                contract_type=contract,
                salary_text=salary,
                published_at=now - timedelta(days=days),
                category_slug=category,
                is_demo=True,
            )
        )
    return cards


def featured_jobs(db: Session, settings: Settings, limit: int = 6) -> list[JobCard]:
    try:
        rows = db.scalars(
            select(Job)
            .where(Job.is_active.is_(True))
            .order_by(Job.published_at.desc().nullslast(), Job.id.desc())
            .limit(limit)
        ).all()
    except Exception:
        rows = []
    if rows:
        return [_to_card(job) for job in rows]
    if settings.is_development:
        return _demo_jobs()[:limit]
    return []


def search_jobs(
    db: Session,
    settings: Settings,
    *,
    q: str = "",
    city: str = "",
    remote_only: bool = False,
    category: str = "",
    limit: int = 20,
) -> list[JobCard]:
    try:
        stmt = select(Job).where(Job.is_active.is_(True))
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where((Job.title.ilike(like)) | (Job.company_name.ilike(like)))
        if city:
            like_city = f"%{city.strip()}%"
            stmt = stmt.where((Job.city.ilike(like_city)) | (Job.state.ilike(like_city)))
        if remote_only:
            stmt = stmt.where(Job.work_mode == "remote")
        if category:
            stmt = stmt.where(Job.category_slug == category)
        rows = db.scalars(stmt.order_by(Job.published_at.desc().nullslast()).limit(limit)).all()
    except Exception:
        rows = []
    if rows:
        return [_to_card(job) for job in rows]
    if settings.is_development:
        jobs = _demo_jobs()
        query = q.lower().strip()
        city_q = city.lower().strip()
        filtered = []
        for job in jobs:
            if query and query not in job.title.lower() and query not in job.company_name.lower():
                continue
            if city_q and city_q not in f"{job.city} {job.state}".lower():
                continue
            if remote_only and job.work_mode != "remote":
                continue
            if category and job.category_slug != category:
                continue
            filtered.append(job)
        return filtered[:limit]
    return []


def category_counts(db: Session) -> dict[str, int]:
    try:
        rows = db.execute(
            select(Job.category_slug, func.count(Job.id))
            .where(Job.is_active.is_(True), Job.category_slug != "")
            .group_by(Job.category_slug)
        ).all()
        return {slug: count for slug, count in rows if slug}
    except Exception:
        return {}


def get_job(db: Session, slug: str, settings: Settings) -> JobCard | None:
    try:
        job = db.scalar(select(Job).where(Job.slug == slug, Job.is_active.is_(True)))
    except Exception:
        job = None
    if job:
        return _to_card(job)
    if settings.is_development:
        for demo in _demo_jobs():
            if demo.slug == slug:
                return demo
    return None
