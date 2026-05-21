from datetime import datetime
from flask import request
from flask_login import current_user
from functools import wraps
from database.db import db
from models.audit_log import AuditLog

def audit_log(acao_default="update", tabela_default="desconhecido"):
    """Decorator para registrar ações de auditoria automaticamente."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Tenta identificar o ID do registro nos argumentos da rota
            registro_id = kwargs.get('prontuario_id') or kwargs.get('id')
            
            usuario_id = getattr(current_user, "id", None) if current_user.is_authenticated else None
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            
            try:
                log = AuditLog(
                    tabela=tabela_default,
                    registro_id=registro_id,
                    acao=acao_default,
                    detalhe=f"Endpoint: {request.endpoint} | Método: {request.method}",
                    usuario_id=usuario_id,
                    ip=ip,
                    criado_em=datetime.utcnow()
                )
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                print(f"[ERRO AUDITORIA]: {e}")
                db.session.rollback()
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator