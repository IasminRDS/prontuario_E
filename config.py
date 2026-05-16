import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _to_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _normalize_database_url(url: str) -> str:
    """
    Compatibiliza URL de banco para SQLAlchemy.
    Ex.: postgres:// -> postgresql://
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class BaseConfig:
    # Ambiente
    APP_NAME = "Prontuário Único"
    APP_ENV = os.getenv("APP_ENV", "prod").strip().lower()
    DEBUG = False
    TESTING = False

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "sus-prontuario-secret-2024-mude-em-producao")

    # Banco
    DEFAULT_SQLITE_PATH = BASE_DIR / "prontuario.db"
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Engine options
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": _to_int(os.getenv("DB_POOL_RECYCLE"), 1800),
        "pool_size": _to_int(os.getenv("DB_POOL_SIZE"), 10),
        "max_overflow": _to_int(os.getenv("DB_MAX_OVERFLOW"), 20),
    }

    # Segurança / sessão
    WTF_CSRF_ENABLED = _to_bool(os.getenv("WTF_CSRF_ENABLED"), False)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _to_bool(os.getenv("SESSION_COOKIE_SECURE"), False)

    # Feature flags (usadas nas rotas)
    FEATURE_DEV_MODE = False
    FEATURE_RBAC_STRICT = True
    FEATURE_ALLOW_CREATE_WITHOUT_UNIT = False
    FEATURE_BYPASS_PACIENTE_SCOPE = False

    # Paginação
    PACIENTES_PER_PAGE = _to_int(os.getenv("PACIENTES_PER_PAGE"), 20)

    # Logs
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def init_app(cls, app):
        # Ajustes específicos de driver (opcional)
        uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if uri.startswith("sqlite"):
            # SQLite não usa pool_size/max_overflow como Postgres
            opts = dict(app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}))
            opts.pop("pool_size", None)
            opts.pop("max_overflow", None)
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = opts


class DevelopmentConfig(BaseConfig):
    APP_ENV = "dev"
    DEBUG = True

    FEATURE_DEV_MODE = True
    FEATURE_RBAC_STRICT = False
    FEATURE_ALLOW_CREATE_WITHOUT_UNIT = True
    FEATURE_BYPASS_PACIENTE_SCOPE = True

    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    APP_ENV = "prod"
    DEBUG = False

    FEATURE_DEV_MODE = False
    FEATURE_RBAC_STRICT = True
    FEATURE_ALLOW_CREATE_WITHOUT_UNIT = False
    FEATURE_BYPASS_PACIENTE_SCOPE = False

    SESSION_COOKIE_SECURE = _to_bool(os.getenv("SESSION_COOKIE_SECURE"), True)


class TestingConfig(BaseConfig):
    APP_ENV = "test"
    TESTING = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False

    FEATURE_DEV_MODE = True
    FEATURE_RBAC_STRICT = False
    FEATURE_ALLOW_CREATE_WITHOUT_UNIT = True
    FEATURE_BYPASS_PACIENTE_SCOPE = True


CONFIG_MAP = {
    "dev": DevelopmentConfig,
    "prod": ProductionConfig,
    "test": TestingConfig,
}


def detect_env() -> str:
    """
    Prioridade:
      1) APP_ENV explícito
      2) Providers (Railway/Render/PRODUCTION)
      3) fallback prod
    """
    explicit = (os.getenv("APP_ENV") or "").strip().lower()
    if explicit in CONFIG_MAP:
        return explicit

    is_production = bool(
        os.getenv("RAILWAY_ENVIRONMENT")
        or os.getenv("RENDER")
        or os.getenv("PRODUCTION")
    )
    return "prod" if is_production else "dev"


def get_config_class(env: str | None = None):
    key = (env or detect_env()).strip().lower()
    return CONFIG_MAP.get(key, ProductionConfig)
