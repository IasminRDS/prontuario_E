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

class BaseConfig:
    # Flask / Segurança
    SECRET_KEY = os.getenv("SECRET_KEY", "KeyToChangeInProduction")
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'key-to-change-in-production'
    WTF_CSRF_ENABLED = _to_bool(os.getenv("WTF_CSRF_ENABLED"), True)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Mude para True se usar HTTPS em produção
    SESSION_COOKIE_SAMESITE = "Lax"

    # Banco de Dados
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/prontuario.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Engine options para estabilidade de conexão
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": _to_int(os.getenv("DB_POOL_RECYCLE"), 1800),
        "pool_size": _to_int(os.getenv("DB_POOL_SIZE"), 10),
        "max_overflow": _to_int(os.getenv("DB_MAX_OVERFLOW"), 20),
    }

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
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    LOG_LEVEL = "INFO"

def get_config_class():
    env = os.getenv("APP_ENV", "dev").strip().lower()
    return {"dev": DevelopmentConfig, "prod": ProductionConfig}.get(env, DevelopmentConfig)