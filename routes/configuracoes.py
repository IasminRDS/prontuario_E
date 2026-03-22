# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.unidade import Unidade
from models.user import User
from database.db import db
from utils.security import admin_requerido
from utils.audit import registrar

configuracoes_bp = Blueprint('configuracoes', __name__, url_prefix='/configuracoes')


@configuracoes_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_requerido
def index():
    unidade = Unidade.query.get(current_user.unidade_id) if current_user.unidade_id else None

    if request.method == 'POST':
        acao = request.form.get('acao')

        if acao == 'unidade' and unidade:
            unidade.nome      = request.form.get('nome', '').strip()
            unidade.cnes      = request.form.get('cnes', '').strip() or None
            unidade.tipo      = request.form.get('tipo', '').strip() or None
            unidade.endereco  = request.form.get('endereco', '').strip() or None
            unidade.municipio = request.form.get('municipio', '').strip() or None
            unidade.uf        = request.form.get('uf', '').strip().upper() or None
            unidade.telefone  = request.form.get('telefone', '').strip() or None
            db.session.commit()
            registrar('unidades', unidade.id, 'update', 'Dados da unidade atualizados')
            flash('Dados da unidade atualizados!', 'success')

        elif acao == 'senha':
            senha_atual = request.form.get('senha_atual', '')
            nova_senha  = request.form.get('nova_senha', '')
            confirma    = request.form.get('confirma_senha', '')
            if not current_user.check_password(senha_atual):
                flash('Senha atual incorreta.', 'danger')
            elif nova_senha != confirma:
                flash('As senhas não coincidem.', 'danger')
            elif len(nova_senha) < 6:
                flash('A nova senha deve ter ao menos 6 caracteres.', 'danger')
            else:
                current_user.set_password(nova_senha)
                db.session.commit()
                registrar('users', current_user.id, 'update', 'Senha alterada')
                flash('Senha alterada com sucesso!', 'success')

        return redirect(url_for('configuracoes.index'))

    total_usuarios  = User.query.filter_by(ativo=True).count()
    total_inativos  = User.query.filter_by(ativo=False).count()

    return render_template('configuracoes/index.html',
                           unidade=unidade,
                           total_usuarios=total_usuarios,
                           total_inativos=total_inativos)


@configuracoes_bp.route('/minha-senha', methods=['GET', 'POST'])
@login_required
def minha_senha():
    """Qualquer usuário pode trocar sua própria senha."""
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        nova_senha  = request.form.get('nova_senha', '')
        confirma    = request.form.get('confirma_senha', '')
        if not current_user.check_password(senha_atual):
            flash('Senha atual incorreta.', 'danger')
        elif nova_senha != confirma:
            flash('As senhas não coincidem.', 'danger')
        elif len(nova_senha) < 6:
            flash('A nova senha deve ter ao menos 6 caracteres.', 'danger')
        else:
            current_user.set_password(nova_senha)
            db.session.commit()
            registrar('users', current_user.id, 'update', 'Senha alterada')
            flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('configuracoes.minha_senha'))

    return render_template('configuracoes/minha_senha.html')
