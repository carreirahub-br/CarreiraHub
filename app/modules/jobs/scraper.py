import logging
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.jobs.models import Job

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

BRAZIL_STATES = {
    "AC": "AC", "AL": "AL", "AP": "AP", "AM": "AM", "BA": "BA",
    "CE": "CE", "DF": "DF", "ES": "ES", "GO": "GO", "MA": "MA",
    "MT": "MT", "MS": "MS", "MG": "MG", "PA": "PA", "PB": "PB",
    "PR": "PR", "PE": "PE", "PI": "PI", "RJ": "RJ", "RN": "RN",
    "RS": "RS", "RO": "RO", "RR": "RR", "SC": "SC", "SP": "SP",
    "SE": "SE", "TO": "TO",
}

CATEGORY_KEYWORDS = {
    "tecnologia": [
        "desenvolvedor", "developer", "software", "python", "java", "frontend",
        "backend", "fullstack", "full stack", "tech", "ti", "dados", "data",
        "devops", "cloud", "qa", "qa engineer", "sistemas", "programador",
        "machine learning", "ia", "ai", "engenharia de software", "react", "node",
        "golang", "c#", ".net", "php", "mobile", "android", "ios",
    ],
    "marketing": [
        "marketing", "growth", "social media", "copywriter", "seo", "crm",
        "comunicação", "publicidade", "designer", "design", "ui", "ux",
        "product manager", "branding", "conteúdo",
    ],
    "financeiro": [
        "financeiro", "financeira", "contábil", "contabilidade", "auditor",
        "fiscal", "faturamento", "tesouraria", "contas a pagar", "contas a receber",
        "custos", "controladoria", "crédito",
    ],
    "administracao": [
        "administrativo", "administrativa", "administração", "recursos humanos",
        "rh", "departamento pessoal", "dp", "secretária", "secretário",
        "recepcionista", "facilities", "compras", "suprimentos",
    ],
    "engenharia": [
        "engenheiro", "engenheira", "engenharia civil", "engenharia mecânica",
        "engenharia elétrica", "engenharia de produção", "engenharia química",
        "autocad", "obras", "projetista",
    ],
    "saude": [
        "enfermagem", "enfermeiro", "enfermeira", "farmacêutico", "farmácia",
        "biomédico", "fisioterapeuta", "psicólogo", "psicóloga", "nutricionista",
        "médico", "médica", "dentista", "odontologia", "veterinário",
    ],
    "logistica": [
        "logística", "estoque", "armazenista", "expedição", "almoxarife",
        "conferente", "frotas", "motorista", "transportes", "supply chain",
    ],
    "atendimento": [
        "atendimento", "suporte", "sac", "help desk", "customer success",
        "teleatendimento", "call center", "ouvidoria", "operador de sac",
    ],
}


def slugify(text: str) -> str:
    """Gera um slug URL-friendly limpo."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    cleaned = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
    return re.sub(r"[-\s]+", "-", cleaned)


def infer_category(title: str, description: str = "") -> str:
    """Classifica a vaga em uma das categorias do CarreiraHub."""
    combined = f"{title} {description}".lower()
    for cat_slug, terms in CATEGORY_KEYWORDS.items():
        for term in terms:
            if re.search(r"\b" + re.escape(term) + r"\b", combined):
                return cat_slug
    return "tecnologia"


def parse_location(location_raw: str, title: str = "") -> tuple[str, str, str]:
    """
    Retorna (cidade, estado, work_mode).
    work_mode: 'remote', 'hybrid', 'onsite'.
    """
    title_lower = title.lower()
    loc_lower = location_raw.lower()

    # Detecta modalidade
    if "remoto" in title_lower or "remote" in title_lower or "remoto" in loc_lower or "remote" in loc_lower:
        work_mode = "remote"
    elif "híbrido" in title_lower or "hibrido" in title_lower or "hybrid" in title_lower or "híbrido" in loc_lower:
        work_mode = "hybrid"
    else:
        work_mode = "onsite"

    city = ""
    state = ""

    parts = [p.strip() for p in location_raw.split(",") if p.strip()]
    if parts:
        # Se contiver apenas 'Brasil' ou 'Brazil'
        if len(parts) == 1 and parts[0].lower() in {"brasil", "brazil", "trabalho remoto", "remote"}:
            if work_mode != "hybrid":
                work_mode = "remote"
            return ("", "", work_mode)

        # Ex: ['Curitiba', 'PR']
        possible_uf = parts[-1].upper()
        if possible_uf in BRAZIL_STATES:
            state = possible_uf
            city = parts[0]
        elif len(parts) >= 2 and parts[-2].upper() in BRAZIL_STATES:
            state = parts[-2].upper()
            city = parts[0]
        else:
            # Não encontrou sigla direta, define a primeira parte como cidade se não for 'Brasil'
            if parts[0].lower() not in {"brasil", "brazil"}:
                city = parts[0]

    return (city, state, work_mode)


def infer_contract_type(title: str, text: str = "") -> str:
    combined = f"{title} {text}".lower()
    if re.search(r"\best[aá]gio\b", combined):
        return "Estágio"
    if re.search(r"\bpj\b", combined):
        return "PJ"
    if re.search(r"\btempor[aá]rio\b", combined):
        return "Temporário"
    return "CLT"


def parse_job_cards_html(html: str) -> list[dict[str, Any]]:
    """Analisa o HTML retornado pelo endpoint de busca de vagas públicas do LinkedIn."""
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_="base-search-card")
    results = []

    for card in cards:
        title_el = card.find("h3", class_="base-search-card__title")
        comp_el = card.find("h4", class_="base-search-card__subtitle")
        loc_el = card.find("span", class_="job-search-card__location")
        link_el = card.find("a", class_="base-card__full-link")
        time_el = card.find("time")
        urn = card.get("data-entity-urn", "")

        title = title_el.get_text(strip=True) if title_el else ""
        company = comp_el.get_text(strip=True) if comp_el else ""
        location_raw = loc_el.get_text(strip=True) if loc_el else ""
        link = link_el.get("href") if link_el else ""
        if link:
            # Remove parâmetros de rastreamento da URL do LinkedIn
            link = link.split("?")[0]

        pub_date_str = time_el.get("datetime") if time_el else ""
        published_at = None
        if pub_date_str:
            try:
                published_at = datetime.fromisoformat(pub_date_str).replace(tzinfo=UTC)
            except (ValueError, TypeError):
                published_at = datetime.now(UTC)
        else:
            published_at = datetime.now(UTC)

        # Extrai o ID numérico do LinkedIn
        linkedin_id = ""
        if "urn:li:jobPosting:" in urn:
            linkedin_id = urn.split("urn:li:jobPosting:")[-1]
        elif link and "/view/" in link:
            match = re.search(r"-(\d+)", link)
            if match:
                linkedin_id = match.group(1)

        if not title or not company:
            continue

        city, state, work_mode = parse_location(location_raw, title)
        category_slug = infer_category(title)
        contract_type = infer_contract_type(title)

        slug_base = f"{slugify(title)}-{slugify(company)}"
        if linkedin_id:
            slug = f"{slug_base}-{linkedin_id}"[:180]
        else:
            slug = slug_base[:180]

        results.append({
            "title": title,
            "company_name": company,
            "city": city,
            "state": state,
            "work_mode": work_mode,
            "contract_type": contract_type,
            "category_slug": category_slug,
            "published_at": published_at,
            "linkedin_id": linkedin_id,
            "external_url": link,
            "slug": slug,
            "salary_text": None,
            "description": "",
        })

    return results


def fetch_linkedin_jobs(
    keywords: str = "tecnologia",
    location: str = "Brasil",
    geo_id: str = "106057199",
    start: int = 0,
    limit: int = 10,
    timeout: float = 12.0,
) -> list[dict[str, Any]]:
    """
    Consome o endpoint público do LinkedIn sem necessidade de login.
    Retorna uma lista de dados de vagas prontos para inserção.
    """
    collected: list[dict[str, Any]] = []
    current_start = start

    while len(collected) < limit:
        params = {
            "keywords": keywords,
            "location": location,
            "geoId": geo_id,
            "start": current_start,
        }
        query_str = urllib.parse.urlencode(params)
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{query_str}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status != 200:
                    logger.warning("LinkedIn retornou status %s", response.status)
                    break
                html = response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            logger.error("Falha ao consultar LinkedIn: %s", e)
            break

        cards = parse_job_cards_html(html)
        if not cards:
            break

        for card in cards:
            collected.append(card)
            if len(collected) >= limit:
                break

        current_start += len(cards)

    return collected


def fetch_job_description(linkedin_id: str, timeout: float = 10.0) -> str:
    """Busca a descrição completa da vaga através do endpoint de detalhe público."""
    if not linkedin_id:
        return ""

    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{linkedin_id}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                html = resp.read().decode("utf-8", errors="replace")
                soup = BeautifulSoup(html, "html.parser")
                desc_el = soup.find("div", class_="show-more-less-html__markup")
                if desc_el:
                    return desc_el.get_text(separator="\n", strip=True)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        logger.debug("Não foi possível buscar a descrição completa da vaga %s: %s", linkedin_id, e)

    return ""


def save_scraped_jobs(
    db: Session,
    jobs_data: list[dict[str, Any]],
    fetch_descriptions: bool = False,
) -> list[Job]:
    """
    Insere ou atualiza as vagas no banco de dados.
    Os registros ficam disponíveis imediatamente no módulo 'Encontrar Vagas'.
    """
    saved_jobs: list[Job] = []

    for item in jobs_data:
        slug = item["slug"]
        existing = db.scalar(select(Job).where(Job.slug == slug))

        description = item.get("description", "")
        if fetch_descriptions and not description and item.get("linkedin_id"):
            description = fetch_job_description(item["linkedin_id"])

        if existing:
            # Atualiza dados existentes mantendo a atividade
            existing.title = item["title"]
            existing.company_name = item["company_name"]
            existing.city = item["city"]
            existing.state = item["state"]
            existing.work_mode = item["work_mode"]
            existing.contract_type = item["contract_type"]
            existing.category_slug = item["category_slug"]
            if description:
                existing.description = description
            existing.is_active = True
            saved_jobs.append(existing)
        else:
            job = Job(
                slug=slug,
                title=item["title"],
                company_name=item["company_name"],
                city=item["city"],
                state=item["state"],
                work_mode=item["work_mode"],
                contract_type=item["contract_type"],
                category_slug=item["category_slug"],
                salary_text=item.get("salary_text"),
                description=description,
                is_active=True,
                published_at=item["published_at"],
            )
            db.add(job)
            saved_jobs.append(job)

    db.commit()
    for j in saved_jobs:
        db.refresh(j)

    return saved_jobs
