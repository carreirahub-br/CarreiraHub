from datetime import UTC, datetime

from app.modules.jobs.scraper import (
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

    city, state, mode = parse_location("Brasil", "Analista")
    assert city == ""
    assert state == ""
    assert mode == "remote"


def test_infer_contract_type():
    assert infer_contract_type("Estágio em TI") == "Estágio"
    assert infer_contract_type("Desenvolvedor PJ") == "PJ"
    assert infer_contract_type("Analista de RH CLT") == "CLT"


def test_parse_job_cards_html():
    sample_html = """
    <div class="base-search-card" data-entity-urn="urn:li:jobPosting:987654321">
        <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/analista-de-dados-987654321?refId=xyz">
            <span class="sr-only">Analista de Dados</span>
        </a>
        <div class="base-search-card__info">
            <h3 class="base-search-card__title">Analista de Dados Pleno</h3>
            <h4 class="base-search-card__subtitle">Tech Corp</h4>
            <div class="base-search-card__metadata">
                <span class="job-search-card__location">Florianópolis, SC</span>
                <time class="job-search-card__listdate" datetime="2026-10-25">3 dias atrás</time>
            </div>
        </div>
    </div>
    """
    parsed = parse_job_cards_html(sample_html)
    assert len(parsed) == 1
    job = parsed[0]
    assert job["title"] == "Analista de Dados Pleno"
    assert job["company_name"] == "Tech Corp"
    assert job["city"] == "Florianópolis"
    assert job["state"] == "SC"
    assert job["category_slug"] == "tecnologia"
    assert job["linkedin_id"] == "987654321"
    assert "tech-corp" in job["slug"]


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
            "salary_text": "R$ 15.000",
            "description": "Responsável por pipelines ETL e modelagem de dados.",
        }
    ]

    saved = save_scraped_jobs(db, jobs_data)
    assert len(saved) == 1
    assert saved[0].id is not None

    # Verifica se o serviço de busca encontra a vaga no banco
    found = search_jobs(db, settings, q="Engenheiro")
    assert len(found) >= 1
    assert any(j.slug == "engenheiro-de-dados-senior-acme-111222333" for j in found)

    # Testa a rota /vagas através do client HTTP
    response = client.get("/vagas")
    assert response.status_code == 200
    assert "Engenheiro de Dados Sênior" in response.text
    assert "Acme BigData" in response.text
    assert "Demonstração" not in response.text  # Já não é demonstração, pois há vagas reais

    # Testa a rota de detalhe /vagas/{slug}
    detail_resp = client.get("/vagas/engenheiro-de-dados-senior-acme-111222333")
    assert detail_resp.status_code == 200
    assert "Responsável por pipelines ETL e modelagem de dados." in detail_resp.text
