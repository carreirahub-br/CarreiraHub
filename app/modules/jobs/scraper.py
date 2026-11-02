import logging
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
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

# Termos que indicam encerramento de candidatura
CLOSED_JOB_MARKERS = [
    "não aceita mais candidaturas",
    "nao aceita mais candidaturas",
    "candidaturas encerradas",
    "no longer accepting applications",
    "vaga encerrada",
    "inscrições encerradas",
    "inscricoes encerradas",
    "closed-job",
    "applications closed",
]

# Mapeamento completo dos estados brasileiros (siglas e nomes por extenso)
STATE_NAME_TO_UF = {
    # Siglas
    "AC": "AC", "AL": "AL", "AP": "AP", "AM": "AM", "BA": "BA",
    "CE": "CE", "DF": "DF", "ES": "ES", "GO": "GO", "MA": "MA",
    "MT": "MT", "MS": "MS", "MG": "MG", "PA": "PA", "PB": "PB",
    "PR": "PR", "PE": "PE", "PI": "PI", "RJ": "RJ", "RN": "RN",
    "RS": "RS", "RO": "RO", "RR": "RR", "SC": "SC", "SP": "SP",
    "SE": "SE", "TO": "TO",
    # Nomes em português
    "acre": "AC", "alagoas": "AL", "amapa": "AP", "amapá": "AP",
    "amazonas": "AM", "bahia": "BA", "ceara": "CE", "ceará": "CE",
    "distrito federal": "DF", "federal district": "DF",
    "espirito santo": "ES", "espírito santo": "ES",
    "goias": "GO", "goiás": "GO", "maranhao": "MA", "maranhão": "MA",
    "mato grosso": "MT", "mato grosso do sul": "MS", "minas gerais": "MG",
    "para": "PA", "pará": "PA", "paraiba": "PB", "paraíba": "PB",
    "parana": "PR", "paraná": "PR", "pernambuco": "PE", "piaui": "PI",
    "piauí": "PI", "rio de janeiro": "RJ", "rio grande do norte": "RN",
    "rio grande do sul": "RS", "rondonia": "RO", "rondônia": "RO",
    "roraima": "RR", "santa catarina": "SC", "sao paulo": "SP",
    "são paulo": "SP", "sergipe": "SE", "tocantins": "TO",
}

# Regiões metropolitanas mapeadas para cidade principal e UF
METRO_REGIONS = {
    "rio de janeiro": ("Rio de Janeiro", "RJ"),
    "sao paulo": ("São Paulo", "SP"),
    "são paulo": ("São Paulo", "SP"),
    "belo horizonte": ("Belo Horizonte", "MG"),
    "curitiba": ("Curitiba", "PR"),
    "porto alegre": ("Porto Alegre", "RS"),
    "recife": ("Recife", "PE"),
    "salvador": ("Salvador", "BA"),
    "fortaleza": ("Fortaleza", "CE"),
    "brasilia": ("Brasília", "DF"),
    "brasília": ("Brasília", "DF"),
    "florianopolis": ("Florianópolis", "SC"),
    "florianópolis": ("Florianópolis", "SC"),
    "campinas": ("Campinas", "SP"),
    "vitoria": ("Vitória", "ES"),
    "vitória": ("Vitória", "ES"),
    "goiania": ("Goiânia", "GO"),
    "goiânia": ("Goiânia", "GO"),
    "manaus": ("Manaus", "AM"),
    "belem": ("Belém", "PA"),
    "belém": ("Belém", "PA"),
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


def is_job_card_accepting(card_el: BeautifulSoup) -> bool:
    """Verifica se o card de vaga ainda está aberto e aceitando candidaturas."""
    classes = " ".join(card_el.get("class", []))
    if "closed" in classes.lower():
        return False

    full_text = card_el.get_text(" ", strip=True).lower()
    for marker in CLOSED_JOB_MARKERS:
        if marker in full_text:
            return False

    return True


def clean_job_title(title: str) -> tuple[str, str | None]:
    """
    Higieniza o título da vaga removendo identificadores internos, referências e sufixos de modalidade.
    Retorna (titulo_limpo, work_mode_hint).
    """
    work_mode_hint = None
    if re.search(r"\b(remote|remoto|trabalho remoto)\b", title, re.IGNORECASE):
        work_mode_hint = "remote"
    elif re.search(r"\b(h[ií]brido|hybrid)\b", title, re.IGNORECASE):
        work_mode_hint = "hybrid"

    cleaned = re.sub(r"\s*[|/]\s*REF#?\s*\S+.*$", "", title, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\s*[-–—]\s*(?:Remote Work|Trabalho Remoto|100%\s*Remoto|Remoto|Remote).*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\s*\((?:Remote Work|Trabalho Remoto|100%\s*Remoto|Remoto|Remote|[A-Za-zÀ-ÿ\s]+-[A-Z]{2})\)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or title, work_mode_hint


def infer_category(title: str, description: str = "") -> str:
    """Classifica a vaga em uma das 8 categorias oficiais do CarreiraHub."""
    combined = f"{title} {description}".lower()
    for cat_slug, terms in CATEGORY_KEYWORDS.items():
        for term in terms:
            if re.search(r"\b" + re.escape(term) + r"\b", combined):
                return cat_slug
    return "tecnologia"


def parse_location(
    location_raw: str,
    title: str = "",
    work_mode_hint: str | None = None,
) -> tuple[str, str, str]:
    """
    Interpreta a localização do LinkedIn e normaliza para o padrão do CarreiraHub.
    Retorna (cidade, estado_uf, work_mode).
    """
    title_lower = title.lower()
    loc_lower = location_raw.lower()

    if work_mode_hint:
        work_mode = work_mode_hint
    elif any(k in title_lower or k in loc_lower for k in ["remoto", "remote"]):
        work_mode = "remote"
    elif any(k in title_lower or k in loc_lower for k in ["híbrido", "hibrido", "hybrid"]):
        work_mode = "hybrid"
    else:
        work_mode = "onsite"

    city = ""
    state = ""

    clean_loc = re.sub(r"^(?:greater|grande)\s+", "", loc_lower).strip()
    clean_loc = re.sub(r"\s+e\s+regi[aã]o$", "", clean_loc).strip()
    if clean_loc in METRO_REGIONS:
        city, state = METRO_REGIONS[clean_loc]
        return (city, state, work_mode)

    parts = [p.strip() for p in location_raw.split(",") if p.strip()]
    if parts:
        if parts[-1].lower() in {"brasil", "brazil"}:
            parts.pop()

        if not parts:
            if work_mode != "hybrid":
                work_mode = "remote"
            return ("", "", work_mode)

        if len(parts) == 1:
            part_clean = parts[0].lower()
            if part_clean in {"trabalho remoto", "remote", "brasil", "brazil"}:
                return ("", "", "remote")
            if part_clean in METRO_REGIONS:
                c, s = METRO_REGIONS[part_clean]
                return (c, s, work_mode)
            city = parts[0]
            return (city, "", work_mode)

        last_part = parts[-1]
        last_lower = last_part.lower()
        if last_part.upper() in STATE_NAME_TO_UF:
            state = STATE_NAME_TO_UF[last_part.upper()]
            city = parts[0]
        elif last_lower in STATE_NAME_TO_UF:
            state = STATE_NAME_TO_UF[last_lower]
            city = parts[0]
        else:
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


def parse_job_cards_html(
    html: str,
    max_days: int = 60,
) -> list[dict[str, Any]]:
    """
    Analisa o HTML retornado pelo LinkedIn, aplicando limpeza de títulos,
    normalização de localidades e filtro estrito dos últimos max_days (padrão 60 dias / 2 meses).
    Garante que a vaga esteja aberta e aceitando candidaturas.
    """
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_="base-search-card")
    results = []
    cutoff_date = datetime.now(UTC) - timedelta(days=max_days)

    for card in cards:
        # Garante que a vaga está aberta e aceitando candidaturas
        if not is_job_card_accepting(card):
            continue

        raw_title_el = card.find("h3", class_="base-search-card__title")
        comp_el = card.find("h4", class_="base-search-card__subtitle")
        loc_el = card.find("span", class_="job-search-card__location")
        link_el = card.find("a", class_="base-card__full-link")
        time_el = card.find("time")
        urn = card.get("data-entity-urn", "")

        raw_title = raw_title_el.get_text(strip=True) if raw_title_el else ""
        company = comp_el.get_text(strip=True) if comp_el else ""
        location_raw = loc_el.get_text(strip=True) if loc_el else ""
        link = link_el.get("href") if link_el else ""
        if link:
            link = link.split("?")[0]

        if not raw_title or not company:
            continue

        pub_date_str = time_el.get("datetime") if time_el else ""
        published_at = None
        if pub_date_str:
            try:
                published_at = datetime.fromisoformat(pub_date_str).replace(tzinfo=UTC)
            except (ValueError, TypeError):
                published_at = datetime.now(UTC)
        else:
            published_at = datetime.now(UTC)

        # Filtro estrito: ignora vagas anteriores a max_days (ex: 60 dias)
        if published_at < cutoff_date:
            continue

        title, work_mode_hint = clean_job_title(raw_title)
        city, state, work_mode = parse_location(location_raw, title, work_mode_hint)
        category_slug = infer_category(title)
        contract_type = infer_contract_type(title)

        linkedin_id = ""
        if "urn:li:jobPosting:" in urn:
            linkedin_id = urn.split("urn:li:jobPosting:")[-1]
        elif link and "/view/" in link:
            match = re.search(r"-(\d+)", link)
            if match:
                linkedin_id = match.group(1)

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
            "salary_text": "A combinar",
            "description": "",
        })

    return results


def fetch_linkedin_jobs(
    keywords: str = "desenvolvedor",
    location: str = "Brasil",
    geo_id: str = "106057199",
    start: int = 0,
    limit: int | None = None,
    max_days: int = 60,
    timeout: float = 12.0,
) -> list[dict[str, Any]]:
    """
    Consome o endpoint público do LinkedIn aplicando filtro de tempo de até 60 dias (f_TPR=r5184000).
    Pagina automaticamente até coletar todas as vagas abertas disponíveis no período ou atingir o limite.
    """
    collected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    current_start = start
    seconds = max_days * 86400
    tpr_filter = f"r{seconds}"

    while True:
        if limit is not None and len(collected) >= limit:
            break

        params = {
            "keywords": keywords,
            "location": location,
            "geoId": geo_id,
            "f_TPR": tpr_filter,
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

        cards = parse_job_cards_html(html, max_days=max_days)
        if not cards:
            break

        new_items = 0
        for card in cards:
            lid = card.get("linkedin_id") or card["slug"]
            if lid in seen_ids:
                continue
            seen_ids.add(lid)
            collected.append(card)
            new_items += 1
            if limit is not None and len(collected) >= limit:
                break

        if new_items == 0:
            break

        current_start += len(cards)

    return collected


def fetch_job_description(linkedin_id: str, timeout: float = 10.0) -> tuple[str, bool]:
    """
    Busca a descrição completa da vaga através do endpoint de detalhe público.
    Retorna (descricao, is_open). Se a vaga foi encerrada no meio tempo, is_open será False.
    """
    if not linkedin_id:
        return ("", True)

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
                html_lower = html.lower()
                for marker in CLOSED_JOB_MARKERS:
                    if marker in html_lower:
                        return ("", False)

                soup = BeautifulSoup(html, "html.parser")
                desc_el = soup.find("div", class_="show-more-less-html__markup")
                if desc_el:
                    return (desc_el.get_text(separator="\n", strip=True), True)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        logger.debug("Não foi possível buscar a descrição completa da vaga %s: %s", linkedin_id, e)

    return ("", True)


def save_scraped_jobs(
    db: Session,
    jobs_data: list[dict[str, Any]],
    fetch_descriptions: bool = False,
) -> list[Job]:
    """
    Insere ou atualiza as vagas no banco de dados.
    Verifica se a vaga continua aberta antes de confirmar.
    """
    saved_jobs: list[Job] = []

    for item in jobs_data:
        slug = item["slug"]
        existing = db.scalar(select(Job).where(Job.slug == slug))

        description = item.get("description", "")
        if fetch_descriptions and not description and item.get("linkedin_id"):
            description, is_open = fetch_job_description(item["linkedin_id"])
            if not is_open:
                if existing:
                    existing.is_active = False
                continue

        if existing:
            existing.title = item["title"]
            existing.company_name = item["company_name"]
            existing.city = item["city"]
            existing.state = item["state"]
            existing.work_mode = item["work_mode"]
            existing.contract_type = item["contract_type"]
            existing.category_slug = item["category_slug"]
            existing.published_at = item["published_at"]
            if item.get("salary_text"):
                existing.salary_text = item["salary_text"]
            if item.get("external_url"):
                existing.external_url = item["external_url"]
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
                salary_text=item.get("salary_text", "A combinar"),
                external_url=item.get("external_url", ""),
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


def check_and_deactivate_closed_jobs(
    db: Session,
    backup_db: Session | None = None,
    batch_size: int = 50,
) -> int:
    """
    Verifica vagas ativas no banco de dados e desativa (is_active = False)
    aquelas que já foram encerradas no LinkedIn ou que passaram de 60 dias.
    Replica a desativação no banco de backup se fornecido.
    Retorna o total de vagas desativadas.
    """
    cutoff_date = datetime.now(UTC) - timedelta(days=60)
    deactivated_count = 0

    # 1. Desativa automaticamente vagas com mais de 60 dias
    old_jobs = db.scalars(
        select(Job).where(Job.is_active.is_(True), Job.published_at < cutoff_date)
    ).all()
    for job in old_jobs:
        job.is_active = False
        deactivated_count += 1
        logger.info("Vaga expirada (>60 dias) desativada: %s", job.slug)

    # 2. Verifica status no LinkedIn para as vagas ativas restantes
    active_jobs = db.scalars(
        select(Job)
        .where(Job.is_active.is_(True))
        .order_by(Job.published_at.asc())
        .limit(batch_size)
    ).all()

    for job in active_jobs:
        linkedin_id = ""
        if job.external_url and "/view/" in job.external_url:
            match = re.search(r"/view/(\d+)", job.external_url)
            if match:
                linkedin_id = match.group(1)
        if not linkedin_id:
            match = re.search(r"-(\d{8,})$", job.slug)
            if match:
                linkedin_id = match.group(1)

        if linkedin_id:
            _, is_open = fetch_job_description(linkedin_id, timeout=8.0)
            if not is_open:
                job.is_active = False
                deactivated_count += 1
                logger.info("Vaga encerrada no LinkedIn desativada: %s", job.title)

    db.commit()

    # 3. Sincroniza a desativação no Supabase se houver
    if backup_db is not None and deactivated_count > 0:
        try:
            deactivated_slugs = [j.slug for j in old_jobs] + [
                j.slug for j in active_jobs if not j.is_active
            ]
            if deactivated_slugs:
                backup_jobs = backup_db.scalars(
                    select(Job).where(Job.slug.in_(deactivated_slugs))
                ).all()
                for bj in backup_jobs:
                    bj.is_active = False
                backup_db.commit()
                logger.info("Desativações replicadas no Supabase com sucesso.")
        except Exception as e:
            logger.warning("Falha ao replicar desativações no banco de backup: %s", e)

    return deactivated_count

