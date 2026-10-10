from app.core.config import Settings, normalize_database_url


def test_normalize_render_postgres_urls():
    assert normalize_database_url("postgres://u:p@host:5432/db").startswith("postgresql+psycopg://")
    assert normalize_database_url("postgresql://u:p@host:5432/db") == "postgresql+psycopg://u:p@host:5432/db"
    assert normalize_database_url("postgresql+psycopg://u:p@host:5432/db") == "postgresql+psycopg://u:p@host:5432/db"


def test_base_url_prefers_custom_domain():
    settings = Settings(app_base_url="https://carreirahub.com.br", render_external_url="https://carreirahub.onrender.com")
    assert settings.base_url == "https://carreirahub.com.br"


def test_base_url_uses_render_when_localhost():
    settings = Settings(app_base_url="http://localhost:8000", render_external_url="https://carreirahub.onrender.com")
    assert settings.base_url == "https://carreirahub.onrender.com"
