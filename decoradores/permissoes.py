# -*- coding: utf-8 -*-
from functools import wraps
from flask import abort, request
from flask_login import current_user

def requer_permissao(nome_permissao):
    """Decorador para verificar permissão específica"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            if not current_user.tem_permissao(nome_permissao):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def requer_acesso_estado(*estados):
    """Decorador para verificar acesso a estado específico"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Se admin, libera para todos
            if current_user.is_admin():
                return f(*args, **kwargs)
            
            # Extrair estado dos parâmetros
            estado = request.view_args.get('estado') or \
                    request.args.get('estado') or \
                    (request.get_json() or {}).get('estado')
            
            if not estado:
                abort(400)
            
            if not current_user.pode_ver_estado(estado):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def requer_acesso_unidade(unidade_id_param='unidade_id'):
    """Decorador para verificar acesso a unidade específica"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Pegar ID da unidade dos parâmetros
            unidade_id = request.view_args.get(unidade_id_param) or \
                        request.args.get(unidade_id_param) or \
                        (request.get_json() or {}).get(unidade_id_param)
            
            if not unidade_id:
                abort(400)
            
            if not current_user.pode_ver_unidade(int(unidade_id)):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def requer_acesso_setor(unidade_id_param='unidade_id', setor_id_param='setor_id'):
    """Decorador para verificar acesso a setor específico"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            unidade_id = request.view_args.get(unidade_id_param) or \
                        request.args.get(unidade_id_param) or \
                        (request.get_json() or {}).get(unidade_id_param)
            
            setor_id = request.view_args.get(setor_id_param) or \
                      request.args.get(setor_id_param) or \
                      (request.get_json() or {}).get(setor_id_param)
            
            if not unidade_id or not setor_id:
                abort(400)
            
            if not current_user.pode_ver_setor(int(unidade_id), int(setor_id)):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def requer_acesso_estadual():
    """Decorador para verificar acesso estadual/nacional"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            if not current_user.pode_ver_estadual():
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator