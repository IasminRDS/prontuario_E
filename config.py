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
    # Busca a chave no arquivo .env. Se não achar, usa uma padrão provisória.
    SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-prontuario-estadual-super-segura")
    
    # Etapa 1.2: Proteção CSRF ativada por padrão
    WTF_CSRF_ENABLED = _to_bool(os.getenv("WTF_CSRF_ENABLED"), True)
    
    # Segurança de Cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Será True em Produção (HTTPS)
    SESSION_COOKIE_SAMESITE = "Lax"

    # Banco de Dados (Etapa 1.1 - Mudança para PostgreSQL)
    # Formato: postgresql://usuario:senha@servidor:porta/nome_do_banco
    DEFAULT_DB_URL = "postgresql://postgres:admin@localhost:5432/prontuario_db"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Engine options para estabilidade de conexão no PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True, # Testa a conexão antes de cada query (evita quedas)
        "pool_recycle": _to_int(os.getenv("DB_POOL_RECYCLE"), 1800),
        "pool_size": _to_int(os.getenv("DB_POOL_SIZE"), 20), # Aumentado para suportar mais requisições
        "max_overflow": _to_int(os.getenv("DB_MAX_OVERFLOW"), 40),
    }

    @classmethod
    def init_app(cls, app):
        # Fallback de segurança caso alguém ainda tente rodar SQLite no ambiente local
        uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if uri.startswith("sqlite"):
            opts = dict(app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}))
            opts.pop("pool_size", None)
            opts.pop("max_overflow", None)
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = opts

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True # Obriga o uso de HTTPS
    LOG_LEVEL = "INFO"

def get_config_class():
    env = os.getenv("APP_ENV", "dev").strip().lower()
    return {"dev": DevelopmentConfig, "prod": ProductionConfig}.get(env, DevelopmentConfig)