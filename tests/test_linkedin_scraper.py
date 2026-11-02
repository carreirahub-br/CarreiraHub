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


def test_parse_job_cards_html_and_60_days_filter():
    now_str = datetime.now(UTC).strftime("%Y-%m-%d")
    days_45_str = (datetime.now(UTC) - timedelta(days=45)).strftime("%Y-%m-%d")
    days_75_str = (datetime.now(UTC) - timedelta(days=75)).strftime("%Y-%m-%d")

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
    <div class="base-search-card" data-entity-urn="urn:li:jobPosting:222222222">
        <div class="base-search-card__info">
            <h3 class="base-search-card__title">Engenheiro de Dados Recente</h3>
            <h4 class="base-search-card__subtitle">Cloud Corp</h4>
            <div class="base-search-card__metadata">
                <span class="job-search-card__location">Curitiba, PR</span>
                <time class="job-search-card__listdate" datetime="{days_45_str}">45 dias atrás</time>
            </div>
        </div>
    </div>
    <div class="base-search-card" data-entity-urn="urn:li:jobPosting:111111111">
        <div class="base-search-card__info">
            <h3 class="base-search-card__title">Vaga Antiga Expirada</h3>
            <h4 class="base-search-card__subtitle">Old Corp</h4>
            <div class="base-search-card__metadata">
                <span class="job-search-card__location">São Paulo, SP</span>
                <time class="job-search-card__listdate" datetime="{days_75_str}">75 dias atrás</time>
            </div>
        </div>
    </div>
    """
    parsed = parse_job_cards_html(sample_html, max_days=60)
    # Vaga de hoje e de 45 dias são mantidas (<= 60 dias). A de 75 dias é descartada.
    assert len(parsed) == 2
    assert parsed[0]["title"] == "Analista de Dados Pleno"
    assert parsed[1]["title"] == "Engenheiro de Dados Recente"


def test_closed_jobs_are_discarded():
    now_str = datetime.now(UTC).strftime("%Y-%m-%d")
    sample_html = f"""
    <div class="base-search-card job-search-card--closed" data-entity-urn="urn:li:jobPosting:333333333">
        <div class="base-search-card__info">
            <h3 class="base-search-card__title">Vaga Fechada por Classe</h3>
            <h4 class="base-search-card__subtitle">Closed Corp</h4>
            <span class="job-search-card__location">São Paulo, SP</span>
            <time class="job-search-card__listdate" datetime="{now_str}">Hoje</time>
        </div>
    </div>
    <div class="base-search-card" data-entity-urn="urn:li:jobPosting:444444444">
        <div class="base-search-card__info">
            <h3 class="base-search-card__title">Vaga Encerrada por Texto</h3>
            <h4 class="base-search-card__subtitle">Closed Corp 2</h4>
            <span class="job-search-card__location">São Paulo, SP</span>
            <span class="status">Não aceita mais candidaturas</span>
            <time class="job-search-card__listdate" datetime="{now_str}">Hoje</time>
        </div>
    </div>
    <div class="base-search-card" data-entity-urn="urn:li:jobPosting:555555555">
        <div class="base-search-card__info">
            <h3 class="base-search-card__title">Vaga Aberta Aceitando</h3>
            <h4 class="base-search-card__subtitle">Open Corp</h4>
            <span class="job-search-card__location">São Paulo, SP</span>
            <time class="job-search-card__listdate" datetime="{now_str}">Hoje</time>
        </div>
    </div>
    """
    parsed = parse_job_cards_html(sample_html, max_days=60)
    assert len(parsed) == 1
    assert parsed[0]["title"] == "Vaga Aberta Aceitando"


def test_pagination_and_selection_of_jobs_per_page(client):
    from app.core.config import get_settings
    from app.core.database import SessionLocal

    db = SessionLocal()
    settings = get_settings()

    # Cria 15 vagas no banco para testar paginação (página 1 com 10 e página 2 com 5)
    jobs_data = [
        {
            "title": f"Desenvolvedor Paginado {i}",
            "company_name": f"Tech Company {i}",
            "city": "São Paulo",
            "state": "SP",
            "work_mode": "onsite",
            "contract_type": "CLT",
            "category_slug": "tecnologia",
            "published_at": datetime.now(UTC),
            "linkedin_id": f"pag-{i}",
            "external_url": f"https://linkedin.com/jobs/view/pag-{i}",
            "slug": f"desenvolvedor-paginado-{i}",
            "salary_text": "A combinar",
            "description": f"Descrição da vaga paginada {i}",
        }
        for i in range(1, 16)
    ]

    saved = save_scraped_jobs(db, jobs_data)
    assert len(saved) == 15

    # Página 1 com 10 vagas por padrão
    page1 = search_jobs(db, settings, page=1, per_page=10)
    assert len(page1) == 10
    assert page1.total == 15
    assert page1.total_pages == 2
    assert page1.has_next is True
    assert page1.has_prev is False

    # Página 2 com as 5 restantes
    page2 = search_jobs(db, settings, page=2, per_page=10)
    assert len(page2) == 5
    assert page2.has_next is False
    assert page2.has_prev is True

    # Teste de seleção de 20 vagas por página
    page_all = search_jobs(db, settings, page=1, per_page=20)
    assert len(page_all) == 15
    assert page_all.total_pages == 1

    # Testa renderização no template via client HTTP
    resp1 = client.get("/vagas?pagina=1&por_pagina=10")
    assert resp1.status_code == 200
    assert "Mostrando" in resp1.text
    assert "10 (padrão: 2x5)" in resp1.text
    assert "Próxima →" in resp1.text

    resp2 = client.get("/vagas?pagina=2&por_pagina=10")
    assert resp2.status_code == 200
    assert "← Anterior" in resp2.text
