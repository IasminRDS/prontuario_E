from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from database.db import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


def _destino_pos_login(user):
    """Redireciona para o destino correto conforme o perfil."""
    if user.is_gestor_estadual():
        return url_for('dash_estadual.index')
    return url_for('dashboard.index')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(_destino_pos_login(current_user))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        user = User.query.filter_by(email=email, ativo=True).first()
        if user and user.check_password(senha):
            login_user(user, remember=True)
            user.ultimo_acesso = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            return redirect(next_page or _destino_pos_login(user))
        else:
            flash('E-mail ou senha inválidos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sessão encerrada com sucesso.', 'info')
    return redirect(url_for('auth.login'))
