import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
        return kwargs
    return {"pool_pre_ping": True}


settings = get_settings()

# Engine Principal (Neon)
engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Engine Backup (Supabase) - configurado apenas se a URL for fornecida
backup_engine = None
BackupSessionLocal = None
if settings.database_backup_url and "[SUA-SENHA-AQUI]" not in settings.database_backup_url:
    try:
        backup_engine = create_engine(settings.database_backup_url, **_engine_kwargs(settings.database_backup_url))
        BackupSessionLocal = sessionmaker(bind=backup_engine, autoflush=False, autocommit=False)
    except Exception as e:
        logger.warning("Falha ao inicializar engine do banco de backup: %s", e)


def get_db() -> Generator[Session, None, None]:
    """
    Fornece uma sessão do banco de dados com failover automático:
    1. Tenta conectar e executar no banco principal (Neon).
    2. Se houver falha de conexão ou o Neon estiver fora do ar, utiliza o Supabase como backup.
    """
    db = SessionLocal()
    use_backup = False

    # Validação rápida de conectividade
    if BackupSessionLocal is not None:
        try:
            db.execute(text("SELECT 1"))
        except (OperationalError, Exception) as e:
            logger.error("⚠️ Banco principal (Neon) inacessível: %s. Chaveando para o Supabase (backup)...", e)
            db.close()
            db = BackupSessionLocal()
            use_backup = True

    try:
        yield db
    except OperationalError as exc:
        if not use_backup and BackupSessionLocal is not None:
            logger.error("⚠️ Erro operacional no banco principal. Tentando failover para Supabase: %s", exc)
            db.close()
            db = BackupSessionLocal()
            yield db
        else:
            raise
    finally:
        db.close()
