from datetime import datetime
from flask import request
from flask_login import current_user

try:
    from database.db import db
except Exception:
    db = None

try:
    from models.audit_log import AuditLog
except Exception:
    AuditLog = None


def registrar(tabela: str, registro_id=None, acao: str = "update", detalhe: str = ""):
    """
    Assinatura padrão usada nas rotas:
      registrar("pacientes", 123, "update", "texto")
    """
    usuario_nome = None
    usuario_id = None

    try:
        if current_user and getattr(current_user, "is_authenticated", False):
            usuario_id = getattr(current_user, "id", None)
            usuario_nome = (
                getattr(current_user, "nome", None)
                or getattr(current_user, "username", None)
                or str(usuario_id or "")
            )
    except Exception:
        pass

    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    except Exception:
        ip = None

    if AuditLog is not None and db is not None:
        try:
            payload = {
                "tabela": tabela,
                "registro_id": registro_id,
                "acao": acao or "update",
                "descricao": detalhe,
                "usuario_id": usuario_id,
                "ip": ip,
                "criado_em": datetime.utcnow(),
            }

            # compatibilidade com modelos diferentes
            if hasattr(AuditLog, "tabela"):
                payload["tabela"] = tabela
            if hasattr(AuditLog, "registro_id"):
                payload["registro_id"] = registro_id
            if hasattr(AuditLog, "detalhe"):
                payload["detalhe"] = detalhe
            elif hasattr(AuditLog, "descricao"):
                payload["descricao"] = detalhe

            if hasattr(AuditLog, "usuario_id"):
                payload["usuario_id"] = usuario_id
            elif hasattr(AuditLog, "usuario"):
                payload["usuario"] = usuario_nome

            item = AuditLog(**payload)
            db.session.add(item)
            db.session.flush()
            return True
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass

    print(
        f"[AUDIT] tabela={tabela} registro_id={registro_id} acao={acao} "
        f"detalhe={detalhe} usuario={usuario_nome} ip={ip}"
    )
    return False
