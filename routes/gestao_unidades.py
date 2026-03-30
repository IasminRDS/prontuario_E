# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.unidade import Unidade
from models.user import User
from database.db import db
from utils.audit import registrar

gestao_unidades_bp = Blueprint('gestao_unidades', __name__, url_prefix='/gestao/unidades')


def _requer_gestor():
    if not current_user.pode_ver_estadual():
        flash('Acesso restrito ao gestor estadual.', 'danger')
        return False
    return True


@gestao_unidades_bp.route('/')
@login_required
def index():
    if not _requer_gestor(): return redirect(url_for('dashboard.index'))
    unidades = Unidade.query.order_by(Unidade.municipio, Unidade.nome).all()
    total_ativas   = sum(1 for u in unidades if u.ativo)
    total_inativas = sum(1 for u in unidades if not u.ativo)
    # Contar usuários e leitos por unidade
    stats = {}
    for u in unidades:
        stats[u.id] = {
            'usuarios': User.query.filter_by(unidade_id=u.id, ativo=True).count(),
        }
    return render_template('gestao_unidades/index.html',
                           unidades=unidades, stats=stats,
                           total_ativas=total_ativas,
                           total_inativas=total_inativas)


@gestao_unidades_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    if not _requer_gestor(): return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        try:
            u = Unidade(
                nome      = request.form.get('nome', '').strip(),
                cnes      = request.form.get('cnes', '').strip() or None,
                tipo      = request.form.get('tipo', '').strip() or None,
                endereco  = request.form.get('endereco', '').strip() or None,
                municipio = request.form.get('municipio', '').strip().upper() or None,
                uf        = request.form.get('uf', '').strip().upper() or None,
                telefone  = request.form.get('telefone', '').strip() or None,
            )
            db.session.add(u)
            db.session.flush()

            # Criar admin local se email fornecido
            email_admin = request.form.get('email_admin', '').strip().lower()
            if email_admin:
                senha = request.form.get('senha_admin', 'admin123')
                admin = User(
                    nome       = request.form.get('nome_admin', 'Administrador').strip(),
                    email      = email_admin,
                    perfil     = 'admin',
                    unidade_id = u.id,
                    ativo      = True,
                )
                admin.set_password(senha)
                db.session.add(admin)

            registrar('unidades', u.id, 'create', f'Unidade {u.nome} cadastrada')
            db.session.commit()
            flash(f'Unidade {u.nome} cadastrada!', 'success')
            return redirect(url_for('gestao_unidades.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')
    return render_template('gestao_unidades/form.html')


@gestao_unidades_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not _requer_gestor(): return redirect(url_for('dashboard.index'))
    u = Unidade.query.get_or_404(id)
    if request.method == 'POST':
        try:
            u.nome     = request.form.get('nome', '').strip()
            u.cnes     = request.form.get('cnes', '').strip() or None
            u.tipo     = request.form.get('tipo', '').strip() or None
            u.endereco = request.form.get('endereco', '').strip() or None
            u.municipio= request.form.get('municipio', '').strip().upper() or None
            u.uf       = request.form.get('uf', '').strip().upper() or None
            u.telefone = request.form.get('telefone', '').strip() or None
            u.ativo    = 'ativo' in request.form
            registrar('unidades', id, 'update', f'Unidade {u.nome} atualizada')
            db.session.commit()
            flash('Unidade atualizada!', 'success')
            return redirect(url_for('gestao_unidades.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')
    return render_template('gestao_unidades/form.html', unidade=u)


@gestao_unidades_bp.route('/<int:id>/usuarios')
@login_required
def usuarios(id):
    if not _requer_gestor(): return redirect(url_for('dashboard.index'))
    u = Unidade.query.get_or_404(id)
    users = User.query.filter_by(unidade_id=id).order_by(User.nome).all()
    return render_template('gestao_unidades/usuarios.html', unidade=u, users=users)
