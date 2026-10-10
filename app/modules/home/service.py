from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.content.schemas import ArticleCard
from app.modules.content.service import recent_articles
from app.modules.jobs.schemas import JobCard
from app.modules.jobs.service import CATEGORIES, category_counts, featured_jobs
from app.modules.notifications.service import INTEREST_OPTIONS


@dataclass(frozen=True)
class CategoryCard:
    slug: str
    name: str
    icon: str
    active_jobs: int | None
    path: str


@dataclass(frozen=True)
class ToolCard:
    slug: str
    name: str
    description: str
    icon: str
    available: bool
    path: str | None
    cta: str


TOOLS = (
    ToolCard(
        slug="curriculo",
        name="Criador de currículo",
        description="Monte um currículo claro, com seções profissionais e exportação em PDF.",
        icon="file",
        available=True,
        path="/curriculo",
        cta="Criar currículo",
    ),
    ToolCard(
        slug="analisador-ats",
        name="Analisador de currículo ATS",
        description="Identifique melhorias de estrutura e palavras-chave para processos seletivos.",
        icon="scan",
        available=False,
        path=None,
        cta="Em breve",
    ),
    ToolCard(
        slug="salario-liquido",
        name="Calculadora de salário líquido",
        description="Estime descontos e o valor líquido a partir da remuneração bruta.",
        icon="calculator",
        available=False,
        path=None,
        cta="Em breve",
    ),
    ToolCard(
        slug="ferias",
        name="Calculadora de férias",
        description="Calcule valores de férias com base no salário e nos dias de descanso.",
        icon="calendar",
        available=False,
        path=None,
        cta="Em breve",
    ),
    ToolCard(
        slug="rescisao",
        name="Simulador de rescisão",
        description="Simule verbas rescisórias de forma educativa, sem substituir orientação jurídica.",
        icon="scale",
        available=False,
        path=None,
        cta="Em breve",
    ),
    ToolCard(
        slug="entrevistas",
        name="Preparação para entrevistas",
        description="Perguntas frequentes e roteiros para se apresentar com mais segurança.",
        icon="messages",
        available=False,
        path=None,
        cta="Em breve",
    ),
)


@dataclass
class HomePageData:
    jobs: list[JobCard]
    categories: list[CategoryCard]
    tools: tuple[ToolCard, ...]
    articles: list[ArticleCard]
    interest_options: list[dict[str, str]]
    jobs_are_demo: bool
    articles_pending: bool


def build_home_page(db: Session, settings: Settings) -> HomePageData:
    jobs = featured_jobs(db, settings)
    counts = category_counts(db)
    categories = [
        CategoryCard(
            slug=item["slug"],
            name=item["name"],
            icon=item["icon"],
            active_jobs=counts.get(item["slug"]),
            path=f"/vagas?categoria={item['slug']}",
        )
        for item in CATEGORIES
    ]
    articles = recent_articles(db)
    return HomePageData(
        jobs=jobs,
        categories=categories,
        tools=TOOLS,
        articles=articles,
        interest_options=INTEREST_OPTIONS,
        jobs_are_demo=bool(jobs) and all(job.is_demo for job in jobs),
        articles_pending=len(articles) == 0,
    )
