from database.db import db
from models.audit_log import AuditLog
from flask import request
from flask_login import current_user

def registrar(tabela, registro_id, acao, descricao=None):
    """Registra uma ação de auditoria. Uso: registrar('pacientes', p.id, 'update', 'Nome alterado')"""
    try:
        ip = request.remote_addr if request else None
        uid = current_user.id if current_user and current_user.is_authenticated else None
        log = AuditLog(
            usuario_id=uid,
            tabela=tabela,
            registro_id=registro_id,
            acao=acao,
            descricao=descricao,
            ip=ip,
        )
        db.session.add(log)
        db.session.flush()   # grava junto com o commit do chamador
    except Exception:
        pass  # auditoria nunca deve quebrar o fluxo principal
