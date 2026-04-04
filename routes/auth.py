from urllib.parse import urlparse, urljoin

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from database.db import db
from models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _is_safe_next_url(target: str) -> bool:
    """
    Garante redirecionamento interno (evita open redirect).
    """
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def _verify_password(user: User, senha: str) -> bool:
    """
    Compatível com diferentes implementações do model User:
    - user.check_password(...)
    - user.verificar_senha(...)
    - user.senha_hash / user.senha + check_password_hash interno do model
    """
    if not senha:
        return False

    if hasattr(user, "check_password") and callable(getattr(user, "check_password")):
        return bool(user.check_password(senha))

    if hasattr(user, "verificar_senha") and callable(getattr(user, "verificar_senha")):
        return bool(user.verificar_senha(senha))

    # fallback mínimo: se não houver método no model, recusa
    return False


@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    # auth_layout=True para base.html esconder sidebar/topbar
    return render_template("auth/login.html", auth_layout=True)


@auth_bp.post("/login")
def login_post():
    # aceita "email" (principal) e fallback para "username"
    identidade = (request.form.get("email") or request.form.get("username") or "").strip().lower()
    senha = request.form.get("senha", "")

    if not identidade or not senha:
        flash("Informe e-mail/usuário e senha.", "warning")
        return redirect(url_for("auth.login", next=request.args.get("next")))

    # busca por e-mail primeiro
    user = User.query.filter(User.email == identidade).first()

    # fallback por username somente se o campo existir no model
    if not user and hasattr(User, "username"):
        user = User.query.filter(User.username == identidade).first()

    if not user:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("auth.login", next=request.args.get("next")))

    if hasattr(user, "ativo") and not user.ativo:
        flash("Usuário inativo.", "danger")
        return redirect(url_for("auth.login", next=request.args.get("next")))

    if not _verify_password(user, senha):
        flash("Senha inválida.", "danger")
        return redirect(url_for("auth.login", next=request.args.get("next")))

    login_user(user, remember=True)

    # atualiza último acesso se existir o campo
    if hasattr(user, "ultimo_acesso"):
        try:
            from datetime import datetime
            user.ultimo_acesso = datetime.utcnow()
            db.session.commit()
        except Exception:
            db.session.rollback()

    flash("Login realizado com sucesso.", "success")

    next_page = request.args.get("next")
    if next_page and _is_safe_next_url(next_page):
        return redirect(next_page)

    return redirect(url_for("dashboard.index"))


@auth_bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for("auth.login"))