from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.core.database import Base, engine
from app.modules.content.models import Article  # noqa: F401
from app.modules.content.router import router as content_router
from app.modules.home.router import router as home_router
from app.modules.jobs.models import Job  # noqa: F401
from app.modules.jobs.router import router as jobs_router
from app.modules.notifications.models import JobAlert  # noqa: F401
from app.modules.notifications.router import router as alerts_router
from app.modules.pages.router import router as pages_router
from app.modules.resumes.router import router as resumes_router
from app.modules.seo.router import router as seo_router

settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, docs_url=None, redoc_url=None, lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax", https_only=not settings.is_development)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(home_router)
app.include_router(jobs_router)
app.include_router(alerts_router)
app.include_router(pages_router)
app.include_router(resumes_router)
app.include_router(content_router)
app.include_router(seo_router)


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}
