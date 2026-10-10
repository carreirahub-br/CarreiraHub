from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.templating import templates
from app.modules.jobs.service import get_job, search_jobs

router = APIRouter()


@router.get("/vagas", include_in_schema=False)
def list_jobs(
    request: Request,
    q: str = Query(default=""),
    cidade: str = Query(default=""),
    remoto: str = Query(default=""),
    categoria: str = Query(default=""),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    remote_only = remoto in {"1", "true", "on", "sim"}
    jobs = search_jobs(
        db,
        settings,
        q=q,
        city=cidade,
        remote_only=remote_only,
        category=categoria,
    )
    return templates.TemplateResponse(
        request,
        "pages/jobs_list.html",
        {
            "jobs": jobs,
            "q": q,
            "cidade": cidade,
            "remoto": remote_only,
            "categoria": categoria,
            "jobs_are_demo": bool(jobs) and all(job.is_demo for job in jobs),
            "meta_title": "Vagas de emprego | CarreiraHub",
            "meta_description": "Pesquise vagas por cargo, cidade e modalidade. Filtre oportunidades remotas e por área de atuação.",
            "canonical_path": "/vagas",
        },
    )


@router.get("/vagas/{slug}", include_in_schema=False)
def job_detail(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    job = get_job(db, slug, settings)
    if job is None:
        return templates.TemplateResponse(
            request,
            "pages/placeholder.html",
            {
                "title": "Vaga não encontrada",
                "intro": "Esta vaga não está disponível ou ainda não foi publicada.",
                "meta_title": "Vaga não encontrada | CarreiraHub",
                "meta_description": "A vaga solicitada não está disponível no CarreiraHub.",
                "canonical_path": f"/vagas/{slug}",
            },
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "pages/job_detail.html",
        {
            "job": job,
            "meta_title": f"{job.title} | CarreiraHub",
            "meta_description": f"Vaga de {job.title} em {job.company_name}. {job.work_mode_label} · {job.contract_type}.",
            "canonical_path": job.detail_path,
            "no_jobposting": True,
        },
    )
