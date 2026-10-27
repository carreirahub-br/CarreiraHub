from datetime import UTC, datetime, timedelta

from app.modules.jobs.scraper import (
    clean_job_title,
    infer_category,
    infer_contract_type,
    parse_job_cards_html,
    parse_location,
    save_scraped_jobs,
    slugify,
)
from app.modules.jobs.service import search_jobs


def test_slugify():
    assert slugify("Desenvolvedor Python Sênior!") == "desenvolvedor-python-senior"
    assert slugify("São Paulo - SP") == "sao-paulo-sp"


def test_clean_job_title():
    clean, mode = clean_job_title("Senior Fullstack Python Developer - Remote Work | REF#305585")
    assert clean == "Senior Fullstack Python Developer"
    assert mode == "remote"

    clean2, mode2 = clean_job_title("Desenvolvedor Delphi SR (Curitiba-PR)")
    assert clean2 == "Desenvolvedor Delphi SR"
    assert mode2 is None


def test_infer_category():
    assert infer_category("Engenheiro de Software Backend") == "tecnologia"
    assert infer_category("Analista de Marketing Digital") == "marketing"
    assert infer_category("Assistente Contábil") == "financeiro"
    assert infer_category("Assistente Administrativo") == "administracao"
    assert infer_category("Enfermeiro Plantonista") == "saude"
    assert infer_category("Engenheiro Civil") == "engenharia"
    assert infer_category("Analista de Logística") == "logistica"
    assert infer_category("Operador de Atendimento ao Cliente") == "atendimento"


def test_parse_location():
    city, state, mode = parse_location("São Paulo, SP", "Desenvolvedor")
    assert city == "São Paulo"
    assert state == "SP"
    assert mode == "onsite"

    city, state, mode = parse_location("Curitiba, PR", "Desenvolvedor Python - Trabalho Remoto")
    assert city == "Curitiba"
    assert state == "PR"
    assert mode == "remote"

    city, state, mode = parse_location("Greater Rio de Janeiro", "Analista")
    assert city == "Rio de Janeiro"
    assert state == "RJ"

    city, state, mode = parse_location("Manaus, Amazonas, Brazil", "Analista")
    assert city == "Manaus"
    assert state == "AM"

    city, state, mode = parse_location("Brasil", "Analista")
    assert city == ""
    assert state == ""
    assert mode == "remote"


def test_infer_contract_type():
    assert infer_contract_type("Estágio em TI") == "Estágio"
    assert infer_contract_type("Desenvolvedor PJ") == "PJ"
    assert infer_contract_type("Analista de RH CLT") == "CLT"


def test_parse_job_cards_html_and_30_days_filter():
    now_str = datetime.now(UTC).strftime("%Y-%m-%d")
    old_str = (datetime.now(UTC) - timedelta(days=45)).strftime("%Y-%m-%d")

    sample_html = f"""
    <div class="base-search-card" data-entity-urn="urn:li:jobPosting:987654321">
        <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/analista-de-dados-987654321?refId=xyz">
            <span class="sr-only">Analista de Dados</span>
        </a>
        <div class="base-search-card__info">
            <h3 class="base-search-card__title">Analista de Dados Pleno | REF#123</h3>
            <h4 class="base-search-card__subtitle">Tech Corp</h4>
            <div class="base-search-card__metadata">
                <span class="job-search-card__location">Florianópolis, SC</span>
                <time class="job-search-card__listdate" datetime="{now_str}">Hoje</time>
            </div>
        </div>
    </div>
    <div class="base-search-card" data-entity-urn="urn:li:jobPosting:111111111">
        <div class="base-search-card__info">
            <h3 class="base-search-card__title">Vaga Antiga Expirada</h3>
            <h4 class="base-search-card__subtitle">Old Corp</h4>
            <div class="base-search-card__metadata">
                <span class="job-search-card__location">São Paulo, SP</span>
                <time class="job-search-card__listdate" datetime="{old_str}">45 dias atrás</time>
            </div>
        </div>
    </div>
    """
    parsed = parse_job_cards_html(sample_html, max_days=30)
    # A vaga de 45 dias atrás deve ser ignorada pelo filtro de 30 dias
    assert len(parsed) == 1
    job = parsed[0]
    assert job["title"] == "Analista de Dados Pleno"
    assert job["company_name"] == "Tech Corp"
    assert job["city"] == "Florianópolis"
    assert job["state"] == "SC"
    assert job["category_slug"] == "tecnologia"
    assert job["linkedin_id"] == "987654321"
    assert job["salary_text"] == "A combinar"


def test_save_and_retrieve_in_vagas_module(client):
    from app.core.config import get_settings
    from app.core.database import SessionLocal

    db = SessionLocal()
    settings = get_settings()

    jobs_data = [
        {
            "title": "Engenheiro de Dados Sênior",
            "company_name": "Acme BigData",
            "city": "Belo Horizonte",
            "state": "MG",
            "work_mode": "remote",
            "contract_type": "CLT",
            "category_slug": "tecnologia",
            "published_at": datetime.now(UTC),
            "linkedin_id": "111222333",
            "external_url": "https://linkedin.com/jobs/view/111222333",
            "slug": "engenheiro-de-dados-senior-acme-111222333",
            "salary_text": "A combinar",
            "description": "Responsável por pipelines ETL e modelagem de dados.",
        }
    ]

    saved = save_scraped_jobs(db, jobs_data)
    assert len(saved) == 1
    assert saved[0].id is not None

    found = search_jobs(db, settings, q="Engenheiro")
    assert len(found) >= 1
    assert any(j.slug == "engenheiro-de-dados-senior-acme-111222333" for j in found)

    response = client.get("/vagas")
    assert response.status_code == 200
    assert "Engenheiro de Dados Sênior" in response.text
    assert "Acme BigData" in response.text
    assert "Demonstração" not in response.text

    detail_resp = client.get("/vagas/engenheiro-de-dados-senior-acme-111222333")
    assert detail_resp.status_code == 200
    assert "Responsável por pipelines ETL e modelagem de dados." in detail_resp.text
