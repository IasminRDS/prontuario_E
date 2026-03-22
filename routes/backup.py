# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, send_file, flash, redirect, url_for, current_app
from flask_login import login_required
from utils.security import admin_requerido
from utils.audit import registrar
from datetime import datetime
import os
import shutil

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')


def _caminho_db():
    """Retorna o caminho absoluto do banco SQLite."""
    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if uri.startswith('sqlite:///'):
        nome = uri.replace('sqlite:///', '')
        if not os.path.isabs(nome):
            return os.path.join(current_app.root_path, nome)
        return nome
    return None


@backup_bp.route('/')
@login_required
@admin_requerido
def index():
    pasta_backup = os.path.join(current_app.root_path, 'backups')
    arquivos = []
    if os.path.exists(pasta_backup):
        for f in sorted(os.listdir(pasta_backup), reverse=True):
            if f.endswith('.db'):
                caminho = os.path.join(pasta_backup, f)
                stat    = os.stat(caminho)
                arquivos.append({
                    'nome':      f,
                    'tamanho':   _fmt_tamanho(stat.st_size),
                    'data':      datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M'),
                    'timestamp': stat.st_mtime,
                })

    db_path  = _caminho_db()
    db_existe = db_path and os.path.exists(db_path)
    db_tam   = _fmt_tamanho(os.stat(db_path).st_size) if db_existe else '—'

    return render_template('backup/index.html',
                           arquivos=arquivos,
                           db_existe=db_existe,
                           db_tam=db_tam)


@backup_bp.route('/criar')
@login_required
@admin_requerido
def criar():
    db_path = _caminho_db()
    if not db_path or not os.path.exists(db_path):
        flash('Banco de dados não encontrado.', 'danger')
        return redirect(url_for('backup.index'))

    pasta_backup = os.path.join(current_app.root_path, 'backups')
    os.makedirs(pasta_backup, exist_ok=True)

    ts   = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(pasta_backup, f'prontuario_backup_{ts}.db')
    shutil.copy2(db_path, dest)
    registrar('backup', None, 'create', f'Backup criado: {os.path.basename(dest)}')
    flash(f'Backup criado: {os.path.basename(dest)}', 'success')
    return redirect(url_for('backup.index'))


@backup_bp.route('/baixar/<nome>')
@login_required
@admin_requerido
def baixar(nome):
    # Sanitizar nome para evitar path traversal
    nome = os.path.basename(nome)
    pasta_backup = os.path.join(current_app.root_path, 'backups')
    caminho = os.path.join(pasta_backup, nome)
    if not os.path.exists(caminho):
        flash('Arquivo não encontrado.', 'danger')
        return redirect(url_for('backup.index'))
    registrar('backup', None, 'view', f'Download backup: {nome}')
    return send_file(caminho, as_attachment=True, download_name=nome)


@backup_bp.route('/excluir/<nome>', methods=['POST'])
@login_required
@admin_requerido
def excluir(nome):
    nome = os.path.basename(nome)
    pasta_backup = os.path.join(current_app.root_path, 'backups')
    caminho = os.path.join(pasta_backup, nome)
    if os.path.exists(caminho):
        os.remove(caminho)
        registrar('backup', None, 'delete', f'Backup excluído: {nome}')
        flash(f'Backup {nome} excluído.', 'info')
    return redirect(url_for('backup.index'))


def _fmt_tamanho(bytes_):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_ < 1024:
            return f'{bytes_:.1f} {unit}'
        bytes_ /= 1024
    return f'{bytes_:.1f} GB'
