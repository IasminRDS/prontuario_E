# -*- coding: utf-8 -*-
import os
from datetime import timedelta

class Config:
    """Configurações base"""
    
    # SECRET KEY
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sus-prontuario-secret-2024-mude-em-producao')
    
    # DATABASE
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///prontuario.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLAlchemy Engine Options (SQLite otimizado)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False},
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Flask
    WTF_CSRF_ENABLED = False
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    
    # Upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = 'uploads'

class DevelopmentConfig(Config):
    """Desenvolvimento"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Produção"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Detectar ambiente
def get_config():
    """Retorna configuração baseada no ambiente"""
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') or \
                   os.environ.get('RENDER') or \
                   os.environ.get('PRODUCTION')
    
    if is_production:
        return ProductionConfig
    return DevelopmentConfig

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}