# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.transferencia import TransferenciaPaciente
from models.paciente import Paciente
from models.internacao import Internacao
from models.unidade import Unidade
from database.db import db
from utils.audit import registrar
from datetime import datetime

transferencia_bp = Blueprint('transferencia', __name__, url_prefix='/transferencia')


@transferencia_bp.route('/')
@login_required
def index():
    uid = current_user.unidade_id
    enviadas  = TransferenciaPaciente.query.filter_by(
        unidade_origem_id=uid).order_by(
        TransferenciaPaciente.data_solicitacao.desc()).limit(30).all()
    recebidas = TransferenciaPaciente.query.filter_by(
        unidade_destino_id=uid).order_by(
        TransferenciaPaciente.data_solicitacao.desc()).limit(30).all()
    pendentes_receber = [t for t in recebidas if t.status == 'solicitada']
    return render_template('transferencia/index.html',
                           enviadas=enviadas, recebidas=recebidas,
                           pendentes_receber=pendentes_receber)


@transferencia_bp.route('/nova', methods=['GET', 'POST'])
@transferencia_bp.route('/nova/<int:paciente_id>', methods=['GET', 'POST'])
@login_required
def nova(paciente_id=None):
    pacientes  = Paciente.query.filter_by(ativo=True).order_by(Paciente.nome).all()
    unidades   = Unidade.query.filter(
        Unidade.ativo == True,
        Unidade.id != current_user.unidade_id
    ).order_by(Unidade.municipio, Unidade.nome).all()
    pac_sel = Paciente.query.get(paciente_id) if paciente_id else None
    internacoes = []
    if pac_sel:
        internacoes = Internacao.query.filter_by(
            paciente_id=pac_sel.id, status='ativa').all()

    if request.method == 'POST':
        try:
            dp_str = request.form.get('data_prevista', '').strip()
            t = TransferenciaPaciente(
                paciente_id        = int(request.form['paciente_id']),
                internacao_id      = request.form.get('internacao_id') or None,
                unidade_origem_id  = current_user.unidade_id,
                unidade_destino_id = int(request.form['unidade_destino_id']),
                solicitado_por     = current_user.id,
                motivo             = request.form.get('motivo', '').strip(),
                cid                = request.form.get('cid', '').strip().upper() or None,
                condicao_transporte= request.form.get('condicao_transporte', '').strip() or None,
                prioridade         = request.form.get('prioridade', 'eletiva'),
                data_prevista      = datetime.strptime(dp_str, '%Y-%m-%dT%H:%M') if dp_str else None,
                resumo_clinico     = request.form.get('resumo_clinico', '').strip() or None,
                observacoes        = request.form.get('observacoes', '').strip() or None,
            )
            db.session.add(t)
            db.session.flush()
            registrar('transferencias_pacientes', t.id, 'create',
                      f'Transferência solicitada para {t.unidade_destino.nome}')
            db.session.commit()
            flash('Transferência solicitada!', 'success')
            return redirect(url_for('transferencia.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')

    return render_template('transferencia/form.html',
                           pacientes=pacientes, unidades=unidades,
                           pac_sel=pac_sel, internacoes=internacoes)


@transferencia_bp.route('/<int:id>')
@login_required
def visualizar(id):
    t = TransferenciaPaciente.query.get_or_404(id)
    return render_template('transferencia/visualizar.html', t=t)


@transferencia_bp.route('/<int:id>/aceitar', methods=['POST'])
@login_required
def aceitar(id):
    t = TransferenciaPaciente.query.get_or_404(id)
    if t.unidade_destino_id != current_user.unidade_id:
        flash('Sem permissão.', 'danger')
        return redirect(url_for('transferencia.index'))
    t.status = 'aceita'
    registrar('transferencias_pacientes', id, 'update', 'Transferência aceita')
    db.session.commit()
    flash('Transferência aceita!', 'success')
    return redirect(url_for('transferencia.index'))


@transferencia_bp.route('/<int:id>/recusar', methods=['POST'])
@login_required
def recusar(id):
    t = TransferenciaPaciente.query.get_or_404(id)
    t.status = 'recusada'
    t.motivo_recusa = request.form.get('motivo_recusa', '').strip() or None
    registrar('transferencias_pacientes', id, 'update', 'Transferência recusada')
    db.session.commit()
    flash('Transferência recusada.', 'info')
    return redirect(url_for('transferencia.index'))


@transferencia_bp.route('/<int:id>/iniciar', methods=['POST'])
@login_required
def iniciar(id):
    t = TransferenciaPaciente.query.get_or_404(id)
    t.status = 'em_transito'
    t.data_saida = datetime.utcnow()
    registrar('transferencias_pacientes', id, 'update', 'Paciente em trânsito')
    db.session.commit()
    flash('Paciente em trânsito!', 'success')
    return redirect(url_for('transferencia.visualizar', id=id))


@transferencia_bp.route('/<int:id>/concluir', methods=['POST'])
@login_required
def concluir(id):
    t = TransferenciaPaciente.query.get_or_404(id)
    t.status = 'concluida'
    t.data_chegada = datetime.utcnow()
    registrar('transferencias_pacientes', id, 'update', 'Transferência concluída')
    db.session.commit()
    flash('Transferência concluída!', 'success')
    return redirect(url_for('transferencia.index'))
